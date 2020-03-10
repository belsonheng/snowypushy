import numpy as np
from pydomo.datasets import ColumnType

class DataSource:
    DOMO = "DOMO"
    HANA = "HANA"
    ORACLE = "ORACLE"
    SNOWFLAKE = "SNOWFLAKE"

    def convert_to_domo_types(source, types):
        results = []
        if source == DataSource.DOMO:
            pass
        elif source == DataSource.HANA:
            pass
        elif source == DataSource.ORACLE:
            pass
        elif source == DataSource.SNOWFLAKE:
            for type in types:
                if type == "FLOAT":
                    results.append(ColumnType.DOUBLE)
                elif type == "NUMBER":
                    results.append(ColumnType.LONG)
                elif "DATE" in type or "TIMESTAMP" in type:
                    results.append(ColumnType.DATETIME)
                else:
                    results.append(ColumnType.STRING)
        return results

    def convert_to_np_types(source, types):
        results = []
        if source == DataSource.DOMO:
            for type in types:
                if type == ColumnType.DOUBLE:
                    results.append(np.float64)
                elif type == ColumnType.LONG:
                    results.append(np.int64)
                elif type == ColumnType.DATETIME:
                    results.append(np.datetime64)
                else:
                    results.append(np.str)
            pass
        elif source == DataSource.HANA:
            pass
        elif source == DataSource.ORACLE:
            pass
        elif source == DataSource.SNOWFLAKE:
            for type in types:
                if type == "FLOAT":
                    results.append(np.float64)
                elif type == "NUMBER":
                    results.append(np.int64)
                else:
                    results.append(np.str)
        return results

    def select_date_columns(columns, types):
        indexes = [i for i in range(len(types)) if "TIMESTAMP" in types[i] or "DATE" in types[i]]
        return [columns[i] for i in indexes]

class Mode:
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
