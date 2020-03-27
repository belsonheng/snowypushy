from snowypushy.features import App
from snowypushy.settings import Configuration
from time import perf_counter
import datetime
import logging

# Configure the logger
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

if __name__ == "__main__":
    start_time = perf_counter()
    app = App(Configuration("sample.yml"), logger_name="demo", log_level=logging.INFO)

    app.logger.info("[SNOWFLAKE] Connecting to {}.{}".format(app.sf_schema, app.sf_table))
    snowflake = app.connect(source=app.DataSource.SNOWFLAKE)
    app.logger.info("Writing data to {}".format(app.download_dir))
    directory = app.download_csv(source=app.DataSource.SNOWFLAKE, engine=snowflake)
    snowflake.close() # except Domo, other connectors need to be closed after usage
    app.logger.info("[DOMO] Connecting to {} ({})".format(app.dataset_name, app.dataset_id if app.dataset_id else "NEW"))
    domo = app.connect(source=app.DataSource.DOMO)
    app.logger.info("[DOMO] Uploading data to {} ({})".format(app.dataset_name, app.dataset_id if app.dataset_id else "NEW"))
    results = app.upload_csv(source=directory, destination=app.DataSource.DOMO, engine=domo, keep=True)
    for i, message in enumerate(results["messages"]):
        if "error" in message:
            app.logger.error("\t-#{}: {}".format(i + 1, message))
    app.logger.info("{} jobs completed and {} died.".format(results["n_completed"], results["n_died"]))

    end_time = perf_counter()
    app.logger.info("Done!")
    app.logger.info("Time Elapsed: {}".format(str(datetime.timedelta(seconds=end_time-start_time))))
