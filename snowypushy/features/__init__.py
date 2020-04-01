from .hvac import Vault
from .connect import Database
from .domo import DomoAPI
from ..common.type import DataSource, Mode

from pydomo.datasets import Schema, Column
from tqdm import tqdm

import json, os
import pandas as pd

import logging

parent_logger = logging.getLogger("snowypushy")
parent_logger.setLevel(logging.WARNING)

class App(object):
    def __init__(self, config, **kwargs):
        if "logger_name" in kwargs:
            self.logger = parent_logger.getChild(kwargs["logger_name"])
        else:
            self.logger = parent_logger
        if kwargs.get("log_level"):
            self.logger.setLevel(kwargs["log_level"])
        self._config = config
        self.DataSource = DataSource
        self.download_dir = config.get("DOWNLOAD_DIR")
        self.chunk_size = config.get("CHUNK_SIZE")
        # snowflake credentials
        if config.get("SF_PASSWORD"):
            self._sf_credentials = "{}:{}".format(config.get("SF_USER"), config.get("SF_PASSWORD"))
        else:
            if config.get("KEEPER_TOKEN"): # keeper vault
                vault = Vault(self.logger).open(
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
            self.logger.exception("Unable to support provided data source: {}".format(source))
            raise Exception("Unable to support provided data source: {}".format(source))
        return Database.connect(connection_string=con, logger=self.logger)

    def merge_csv(self, source, filename):
        try:
            import glob
            filename = filename + ".csv" if not ".csv" in filename else filename
            df = pd.concat([pd.read_csv(f) for f in glob.glob(source + "/*.csv")])
            df.to_csv("{}/{}".format(source, filename), index=False)
        except Exception:
            self.logger.exception("Unable to merge CSV")

    def download_csv(self, source, engine, **kwargs):
        try:
            destination = kwargs["destination"] if "destination" in kwargs else self.download_dir
            if source == DataSource.DOMO:
                destination = destination + self.dataset_name + "/"
                if self.dataset_id:
                    domo = DomoAPI(self.logger, engine)
                    dataset = domo.datasets.get(self.dataset_id)
                    self.logger.info(dataset)
                    if not os.path.exists(destination):
                        os.mkdir(destination)
                    if not os.path.exists(destination + "parts"):
                        os.mkdir(destination + "parts")
                    domo.download_to_csv_file(self.dataset_id, destination + "parts/1.csv")
                    return destination
                else:
                    self.logger.warning("Please provide Dataset ID in config file")
                    raise Exception("Please provide Dataset ID in config file")
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
                    self.logger.warning("Please provide either Table Name or View Name in config file")
                    raise Exception("Please provide either Table Name or View Name in config file")
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
                self.logger.warning("Unable to support provided data source: {}".format(source))
                raise Exception("Unable to support provided data source: {}".format(source))
            self.total_records = engine.execute("SELECT COUNT(1) FROM {}.{}".format(schema, table)).fetchone()[0]
            self.logger.info("Total records: {}".format(self.total_records))
            results = engine.execute(sql).fetchall()
            columns = [{result[0]:result[1]} for result in results]
            if not os.path.exists(destination):
                os.mkdir(destination)
            if not os.path.exists(destination + "parts"):
                os.mkdir(destination + "parts")
            with open(destination + "metadata.json", "w") as file:
                if not self.dataset_name:
                    self.dataset_name = "{}.{}".format(schema, table)
                json.dump({
                    "source": source,
                    "table": "{}.{}".format(schema, table),
                    "rows": int(self.total_records),
                    "columns": [next(iter(column)) for column in columns],
                    "types": [column[next(iter(column))] for column in columns]
                }, file, indent=4)
            self.logger.info("{} Columns: {}".format(len(columns), columns))
            chunks = pd.read_sql(
                sql="SELECT * FROM {}.{}".format(schema, table),
                con=engine,
                chunksize=self.chunk_size
            )
            with tqdm(total=self.total_records, unit="record") as pbar:
                for i, chunk in enumerate(chunks):
                    chunk.to_csv(f"{destination}/parts/{i + 1}.csv", encoding="utf-8", index=False, header=True, mode="w")
                    pbar.update(len(chunk))
            if "merge" in kwargs and kwargs["merge"]:
                self.merge_csv(source, table)
            return destination
        except Exception:
            self.logger.exception("Unable to download CSV")

    def upload_csv(self, source, destination, engine, **kwargs):
        with open(source + "/metadata.json") as file:
            data = json.load(file)
            data_source = data["source"]
            table = data["table"]
            rows = data["rows"]
            columns = list(data["columns"])
            types = list(data["types"])
        if destination == DataSource.DOMO:
            domo = DomoAPI(self.logger, engine)
            if not self.dataset_id:
                # Create a new Dataset Schema
                if not self.dataset_name:
                    self.dataset_name = table
                schema = dict(zip(columns, DataSource.convert_to_domo_types(source=data_source, types=types)))
                dsr = domo.create_dataset(
                    schema=Schema([Column(schema[col], col) for col in schema]),
                    name=self.dataset_name,
                    description=self.dataset_desc
                )
            else:
                # Get existing Dataset Schema
                dsr = domo.get_dataset(self.dataset_id)
            # Search for existing Stream
            streams = domo.search_stream(self.dataset_name)
            # Build a Stream Request
            update_method = "APPEND" if "part" in kwargs else self.update_method
            domo.stream = streams[0] if streams else domo.create_stream(dsr, update_method)
            self.dataset_id = domo.stream["dataSet"]["id"]
            self.logger.info(f"Stream created: {domo.stream}")
            # Create an Execution
            domo.execution = domo.create_execution(domo.stream)
            self.logger.info(f"Execution created: {domo.execution}")
            # Begin upload process
            results = domo.upload_to_domo(
                mode=Mode.PARALLEL,
                source=source + "/parts",
                columns=columns,
                np_types=DataSource.convert_to_np_types(source=data_source, types=types),
                date_columns=DataSource.select_date_columns(columns, types),
                total_records=self.chunk_size if "part" in kwargs else rows,
                chunk_size=self.chunk_size,
                part=kwargs["part"] if "part" in kwargs else None
            )
        # elif destination == DataSource.HANA:
        #     pass
        # elif destination == DataSource.ORACLE:
        #     pass
        # elif destination == DataSource.SNOWFLAKE:
        #     pass
        else:
            self.logger.exception("Unable to support provided data destination: {}".format(destination))
            raise Exception("Unable to support provided data destination: {}".format(destination))
        if "merge" in kwargs and kwargs["merge"]:
            self.merge_csv(source, table)
        if "keep" in kwargs and not kwargs["keep"]:
            import shutil
            shutil.rmtree(source)
        return results
