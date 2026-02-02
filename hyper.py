from tableauhyperapi import HyperProcess, Connection, Telemetry
import pandas as pd

hyper_file_path = "federated_0el9uns13p3nkt1e3poxg1.hyper"

with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    with Connection(hyper.endpoint, hyper_file_path) as connection:
        
        # 1. List schemas
        schemas = connection.catalog.get_schema_names()
        print("Schemas:", schemas)

        # 2. List tables
        tables = connection.catalog.get_table_names("Extract")
        print("Tables:", tables)

        # 3. Read data from first table
        table_name = tables[0]
        query = f'SELECT * FROM {table_name}'
        rows = connection.execute_list_query(query)

        df = pd.DataFrame(rows)
        print(df)
