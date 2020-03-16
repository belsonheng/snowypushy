from snowypushy.features import App
from snowypushy.settings import Configuration
from time import perf_counter
import datetime

if __name__ == "__main__":
    start_time = perf_counter()
    app = App(Configuration("config.yml"))

    print("[SNOWFLAKE] Connecting to {}.{}".format(app.sf_schema, app.sf_table))
    snowflake = app.connect(source=app.DataSource.SNOWFLAKE)
    print("Writing data to {}:".format(app.download_dir))
    directory = app.download_csv(source=app.DataSource.SNOWFLAKE, engine=snowflake)
    snowflake.close() # except Domo, other connectors need to be closed after usage
    print("[DOMO] Connecting to {} ({})".format(app.dataset_name, app.dataset_id if app.dataset_id else "NEW"))
    domo = app.connect(source=app.DataSource.DOMO)
    print("[DOMO] Uploading data to {} ({})".format(app.dataset_name, app.dataset_id if app.dataset_id else "NEW"))
    results = app.upload_csv(source=directory, destination=app.DataSource.DOMO, engine=domo, keep=False)
    for i, message in enumerate(results["messages"]):
        if "error" in message:
            print("\t-#{}: {}".format(i + 1, message))
    print("{} jobs completed and {} died.".format(results["n_completed"], results["n_died"]))

    end_time = perf_counter()
    print("Done!")
    print("Time Elapsed: {}".format(str(datetime.timedelta(seconds=end_time-start_time))))
