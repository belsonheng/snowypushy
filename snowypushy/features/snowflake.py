import glob
import sys
import pandas as pd

from ..common.type import Mode

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from tqdm import tqdm

class SnowflakeAPI(object):
    def __init__(self, logger, snowflake, schema, table, **kwargs):
        self.logger = logger
        self.snowflake = snowflake
        self.schema = schema
        self.table = table

    def _upload(self, part_id, data):
        try:
            data.to_sql(self.table.lower(), self.snowflake, index=False, if_exists="append")
            return f"Part {part_id} uploaded succesfully to SNOWFLAKE."
        except Exception as err:
            return f"Part {part_id} upload met with unexpected error: {err}"

    def upload(self, mode, source, columns, np_types, date_columns, total_records, **kwargs):
        try:
            chunk_size = kwargs["chunk_size"] if "chunk_size" in kwargs else 1024
            results = []
            total_files = 1 if kwargs["part"] else len(glob.glob(f"{source}/*.csv"))
            if mode == Mode.SEQUENTIAL:
                with tqdm(total=total_records, unit="record") as pbar:
                    for i in range(total_files):
                        data = pd.read_csv(
                            "{}/{}.csv".format(source, kwargs["part"] if kwargs["part"] else i + 1),
                            header=0,
                            names=columns,
                            encoding="utf-8",
                            dtype=dict(zip(columns, np_types)),
                            parse_dates=date_columns
                        )
                        results.append(self._upload(i+1, data))
                        pbar.update(len(data))
                completed = [1 for result in results if "succesfully" in result]
                died = [1 for result in results if "error" in result]
                return { "messages": results, "n_completed": len(completed), "n_died": len(died) }
            else:
                raise Exception("Mode: {} not supported.".format(mode))
        except Exception:
            self.logger.exception("Unable to sequential upload to Snowflake")
