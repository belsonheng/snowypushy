from .hvac import Vault
from .connect import Database
from .domo import DomoAPI
from ..common.type import DataSource, Mode

from pydomo.datasets import Schema, Column
from tqdm import tqdm

import json, os, sys
import pandas as pd

class App(object):
    def __init__(self, config):
        self._config = config
        self.DataSource = DataSource
        self.download_dir = config.get("DOWNLOAD_DIR")
        self.chunk_size = config.get("CHUNK_SIZE")
        # snowflake credentials
        if config.get("SF_PASSWORD"):
            self._sf_credentials = "{}:{}".format(config.get("SF_USER"), config.get("SF_PASSWORD"))
        else:
            if config.get("KEEPER_TOKEN"): # keeper vault
                vault = Vault().open(
                    keeper_url=config.get("KEEPER_URL"),
                    keeper_ns=config.get("KEEPER_NS"),
                    keeper_token=config.get("KEEPER_TOKEN"),
                    keeper_password_path=config.get("KEEPER_PASSWORD_PATH"),
                    keeper_secret_path = config.get("KEEPER_SECRET_PATH")
                )
                self._sf_credentials = "{}:{}".format(config.get("SF_USER"), vault["password"])
        self._sf_server = "{}/{}/{}".format(config.get("SF_ACCOUNT"), config.get("SF_DB"), config.get("SF_SCHEMA"))
        self._sf_options = "numpy=True&role={}&warehouse={}".format(config.get("SF_ROLE"), config.get("SF_WH"))
        self.sf_schema = config.get("SF_SCHEMA")
        self.sf_table = config.get("SF_TABLE")
        # domo credentials
        self._domo_client_id = config.get("DOMO_CLIENT_ID")
        self._domo_client_secret = config.get("DOMO_CLIENT_SECRET")
        self.dataset_id = config.get("DATASET_ID")
        self.dataset_name = config.get("DATASET_NAME")
        self.dataset_desc = config.get("DATASET_DESC")
        self.update_method = config.get("UPDATE_METHOD")
        # oracle credentials
        self._oracle_credentials = "{}:{}".format(config.get("ORACLE_USER"), config.get("ORACLE_PASSWORD"))
        self._oracle_server = "{}:{}".format(config.get("ORACLE_HOST"), config.get("ORACLE_PORT"))
        self._oracle_db = config.get("ORACLE_DB")
        self.oracle_schema = config.get("ORACLE_SCHEMA")
        self.oracle_table = config.get("ORACLE_TABLE")
        # hana credentials
        self._hana_credentials = "{}:{}".format(config.get("HANA_USER"), config.get("HANA_PASSWORD"))
        self._hana_server = "{}:{}".format(config.get("HANA_HOST"), config.get("HANA_PORT"))
        self._hana_db = config.get("HANA_DB")
        self.hana_schema = config.get("HANA_SCHEMA")
        self.hana_table = config.get("HANA_TABLE")
        self.hana_view = config.get("HANA_VIEW")

    def connect(self, source):
        if source == DataSource.DOMO:
            return Database.connect(client_id=self._domo_client_id, client_secret=self._domo_client_secret)
        elif source == DataSource.HANA:
            con = "{}://{}@{}/{}".format(
                "hana",
                self._hana_credentials,
                self._hana_server,
                self._hana_db
            )
        elif source == DataSource.ORACLE:
            con = "{}://{}@{}/{}".format(
                "oracle",
                self._oracle_credentials,
                self._oracle_server,
                self._oracle_db
            )
        elif source == DataSource.SNOWFLAKE:
            con = "{}://{}@{}?{}".format(
                "snowflake",
                self._sf_credentials,
                self._sf_server,
                self._sf_options
            )
        else:
            raise Exception("Unable to support provided data source: {}".format(source))
        return Database.connect(connection_string=con)

    def download_csv(self, source, engine, **kwargs):
        try:
            destination = kwargs["destination"] if "destination" in kwargs else self.download_dir
            if source == DataSource.DOMO:
                destination = destination + self.dataset_name + "/"
                if self.dataset_id:
                    domo = DomoAPI(engine)
                    dataset = domo.datasets.get(self.dataset_id)
                    print(dataset)
                    if not os.path.exists(destination):
                        os.mkdir(destination)
                    domo.download_to_csv_file(self.dataset_id, destination + "data.csv")
                    return destination
                else:
                    raise Exception("Please provide Dataset ID in config file.")
            elif source == DataSource.HANA:
                schema = self.hana_schema
                table = self.hana_table
                view = self.hana_view
                if table:
                    destination = destination + self.hana_table + "/"
                    sql = """
                        SELECT COLUMN_NAME, DATA_TYPE_NAME
                        FROM TABLE_COLUMNS
                        WHERE SCHEMA_NAME='{}' AND TABLE_NAME='{}'
                        ORDER BY POSITION;
                    """.format(schema, table)
                elif view:
                    destination = destination + self.hana_view + "/"
                    sql = """
                        SELECT COLUMN_NAME, DATA_TYPE_NAME
                        FROM VIEW_COLUMNS
                        WHERE SCHEMA_NAME='{}' AND VIEW_NAME='{}'
                        ORDER BY POSITION;
                    """.format(schema, view)
                else:
                    raise Exception("Please provide either Table Name or View Name in config file.")
            elif source == DataSource.ORACLE:
                destination = destination + self.oracle_table + "/"
                schema = self.oracle_schema
                table = self.oracle_table
                sql = """
                    SELECT COLUMN_NAME, DATA_TYPE
                    FROM ALL_TAB_COLS
                    WHERE OWNER='{}'
                    AND TABLE_NAME='{}'
                    ORDER BY INTERNAL_COLUMN_ID
                """.format(schema, table)
            elif source == DataSource.SNOWFLAKE:
                destination = destination + self.sf_table + "/"
                schema = self.sf_schema
                table = self.sf_table
                sql = """
                    SELECT COLUMN_NAME, DATA_TYPE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME='{}'
                    ORDER BY ORDINAL_POSITION
                """.format(table)
            else:
                raise Exception("Unable to support provided data source: {}".format(source))

            self.total_records = engine.execute("SELECT COUNT(1) FROM {}.{}".format(schema, table)).fetchone()[0]
            print("Total records: {}".format(self.total_records))
            results = engine.execute(sql).fetchall()
            columns = [{result[0]:result[1]} for result in results]

            if not os.path.exists(destination):
                os.mkdir(destination)
            with open(destination + "metadata.json", "w") as file:
                if not self.dataset_name:
                    self.dataset_name = "{}.{}".format(schema, table)
                json.dump({
                    "source": source,
                    "table": "{}.{}".format(schema, table),
                    "columns": [next(iter(column)) for column in columns],
                    "types": [column[next(iter(column))] for column in columns]
                }, file, indent=4)

            print("{} Columns: {}".format(len(columns), columns))
            chunks = pd.read_sql(
                sql="SELECT * FROM {}.{}".format(schema, table),
                con=engine,
                chunksize=self.chunk_size
            )
            with tqdm(total=self.total_records, unit="record") as pbar:
                for i, chunk in enumerate(chunks):
                    chunk.to_csv(f"{destination}/{i + 1}.csv", encoding="utf-8", index=False, header=True, mode="w")
                    pbar.update(len(chunk))
            return destination
        except Exception as err:
            print("Unable to download CSV:")
            sys.exit(err)

    def upload_csv(self, source, destination, engine, **kwargs):
        with open(source + "/metadata.json") as file:
            data = json.load(file)
            data_source = data["source"]
            table = data["table"]
            columns = list(data["columns"])
            types = list(data["types"])
        if destination == DataSource.DOMO:
            if not self.dataset_id:
                # Create a new Dataset Schema
                if not self.dataset_name:
                    self.dataset_name = table
                schema = dict(zip(columns, DataSource.convert_to_domo_types(source=data_source, types=types)))
                dsr = DomoAPI(engine).create_dataset(
                    schema=Schema([Column(schema[col], col) for col in schema]),
                    name=self.dataset_name,
                    description=self.dataset_desc
                )
            else:
                # Get existing Dataset Schema
                dsr = DomoAPI(engine).get_dataset(self.dataset_id)
            # Build a Stream Request
            stream = DomoAPI(engine).create_stream(dsr, self.update_method)
            self.dataset_id = stream["dataSet"]["id"]
            print(f"Stream created: {stream}")
            # Create an Execution
            execution = DomoAPI(engine).create_execution(stream)
            print(f"Execution created: {execution}")
            # Begin upload process
            results = DomoAPI(engine, stream=stream, execution=execution).upload_to_domo(
                mode=Mode.PARALLEL,
                source=source,
                columns=columns,
                np_types=DataSource.convert_to_np_types(source=data_source, types=types),
                date_columns=DataSource.select_date_columns(columns, types),
                total_records=self.total_records,
                chunk_size=self.chunk_size
            )
            if "keep" in kwargs and not kwargs["keep"]:
                import shutil
                shutil.rmtree(source)
            if "merge" in kwargs and kwargs["merge"]:
                pass
            return results
        # elif destination == DataSource.HANA:
        #     pass
        # elif destination == DataSource.ORACLE:
        #     pass
        # elif destination == DataSource.SNOWFLAKE:
        #     pass
        else:
            raise Exception("Unable to support provided data destination: {}".format(destination))
