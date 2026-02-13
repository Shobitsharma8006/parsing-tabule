from app.parsers.base_parser import BaseParser
import re


class SchemaParser(BaseParser):

    INTERNAL_TABLE_PATTERN = re.compile(r"^_[A-F0-9]{32}$", re.IGNORECASE)

    def _clean(self, value):
        if not value:
            return None
        return value.strip("[]")

    def _is_internal_table(self, table_name: str) -> bool:
        if table_name.startswith("_"):
            return True
        if self.INTERNAL_TABLE_PATTERN.match(table_name):
            return True
        if "_ID_" in table_name.upper():
            return True
        return False

    def parse(self) -> dict:
        self.log_start()

        tables = {}
        custom_sql_map = {}

        try:
            # -----------------------------------------
            # 1️⃣ Capture Custom SQL queries
            # -----------------------------------------
            for rel in self.root.findall(".//relation[@type='text']"):
                name = rel.attrib.get("name")
                sql = (rel.text or "").strip()

                if name and sql:
                    custom_sql_map[name] = sql

            # -----------------------------------------
            # 2️⃣ Parse columns (existing logic)
            # -----------------------------------------
            for record in self.root.findall(".//metadata-record[@class='column']"):
                parent = self._clean(record.findtext("parent-name"))
                column = self._clean(record.findtext("local-name"))
                datatype = record.findtext("local-type")

                if not parent or not column:
                    continue

                if self._is_internal_table(parent):
                    continue

                if parent not in tables:
                    tables[parent] = {
                        "table_name": parent,
                        "query": custom_sql_map.get(parent),  # 👈 KEY LINE
                        "columns": {}
                    }

                if column not in tables[parent]["columns"]:
                    tables[parent]["columns"][column] = {
                        "datatype": datatype or "unknown"
                    }

            # -----------------------------------------
            # 3️⃣ Final shaping
            # -----------------------------------------
            clean_tables = []
            total_columns = 0

            for table in tables.values():
                columns = [
                    {"name": name, "datatype": meta["datatype"]}
                    for name, meta in table["columns"].items()
                ]

                total_columns += len(columns)

                entry = {
                    "table_name": table["table_name"]
                }

                if table.get("query"):
                    entry["query"] = table["query"]  # 👈 placed before columns

                entry["columns"] = columns

                clean_tables.append(entry)

            self.log_complete({
                "table_count": len(clean_tables),
                "total_column_count": total_columns
            })

            return {
                "tables": clean_tables,
                "stats": {
                    "table_count": len(clean_tables),
                    "total_column_count": total_columns
                }
            }

        except Exception as e:
            self.log_error(e)
            raise
