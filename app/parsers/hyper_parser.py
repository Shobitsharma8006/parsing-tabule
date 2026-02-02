from tableauhyperapi import HyperProcess, Connection, Telemetry

class HyperParser:
    def __init__(self, hyper_path: str):
        self.hyper_path = hyper_path

    def parse(self) -> dict:
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
            with Connection(endpoint=hyper.endpoint, database=self.hyper_path) as conn:
                schemas = conn.catalog.get_schema_names()
                tables = []

                for schema in schemas:
                    for table in conn.catalog.get_table_names(schema):
                        tables.append(f"{schema}.{table.name}")

                return {
                    "hyper_file": self.hyper_path,
                    "schemas": schemas,
                    "tables": tables
                }
