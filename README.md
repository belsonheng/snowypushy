# Hi, I'm Snowy and I can be very pushy (in a _good_ way)! :sunglasses:

I'm here to help you with all your data migration woes - grabbing data, saving into CSV files and then pushing all these to another database. But right now, I only understand Snowflake, Oracle, SAP Hana and Domo. If my owner has time to play with me, he might upgrade my skillset and connectivity . Otherwise, you can also teach me a thing or two by contributing to this repository.

To get me working, you got to first tell me everything you know in a configuration file using YAML:

```
# keeper security vault
KEEPER_URL: ""
KEEPER_NS: ""
KEEPER_TOKEN: ""
KEEPER_SECRET_PATH: ""
KEEPER_PASSWORD_PATH: ""

# snowflake configurations
SF_ACCOUNT: ""
SF_SVC_USER: ""
SF_PASSWORD: ""
SF_WH: ""
SF_SCHEMA: ""
SF_DB: ""
SF_ROLE: ""
SF_TABLE: ""

# domo dataset information
DOMO_CLIENT_ID: ""
DOMO_CLIENT_SECRET: ""
DATASET_ID: ""
DATASET_NAME: ""
DATASET_DESC: ""
UPDATE_METHOD: "REPLACE" # "APPEND"
DOWNLOAD_DIR: ""
CHUNK_SIZE: 5000

# oracle credentials
ORACLE_USER: ""
ORACLE_PASSWORD: ""
ORACLE_HOST: ""
ORACLE_PORT: 
ORACLE_DB: ""
ORACLE_SCHEMA: ""
ORACLE_TABLE: ""

# hana credentials
HANA_USER: ""
HANA_PASSWORD: ""
HANA_HOST: ""
HANA_PORT: 
HANA_DB: ""
HANA_SCHEMA: ""
HANA_TABLE: ""
HANA_VIEW: ""
```
If you're using [Keeper Security Vault](https://keepersecurity.com/vault/) to safekeep your password and private key, you have to fill up all the keeper-related configurations. Otherwise, just leave that blank and I will handle the rest :wink:

# Getting Started
```
pip install snowypushy
```

# Connecting to Database
Just set me up with the file path to your configuration file, and I will return you the respective _engine_:
```
from snowypushy.features import App
from snowypushy.settings import Configuration

app = App(Configuration("sample.yml"))

domo = app.connect(source=app.DataSource.DOMO)
hana = app.connect(source=app.DataSource.HANA)
oracle = app.connect(source=app.DataSource.ORACLE)
snowflake = app.connect(source=app.DataSource.SNOWFLAKE)

# do anything you like

# except Domo, other connectors need to be closed after usage
hana.close()
oracle.close()
snowflake.close() 
```

# Downloading to local directory
If you don't tell me which directory to save the CSVs, I will just refer to ```DOWNLOAD_DIR``` in the configuration file.
```
directory = app.download_csv(source=app.DataSource.DOMO, engine=domo)
directory = app.download_csv(source=app.DataSource.HANA, engine=hana)
directory = app.download_csv(source=app.DataSource.ORACLE, engine=oracle)
directory = app.download_csv(source=app.DataSource.SNOWFLAKE, engine=snowflake)
```

# Uploading to Database
I can only push to Domo right now :neutral_face:

Specify ```keep=True``` if you'd like to retain the download CSV files, or I will help you remove them after I'm done uploading.
```
results = app.upload_csv(source=directory, destination=app.DataSource.DOMO, engine=domo, keep=False)
```
As I'm trained to be more productive and efficient, I'm actually spawning threads to distribute my workload. So, you can iterate through the results, check if there's any job that died and "resurrect" them again.
```
for i, message in enumerate(results["messages"]):
    if "error" in message:
        print("\t-#{}: {}".format(i + 1, message))
print("{} jobs completed and {} died.".format(results["n_completed"], results["n_died"]))
```
