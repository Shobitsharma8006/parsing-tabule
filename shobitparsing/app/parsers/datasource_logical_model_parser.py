
from app.parsers.base_parser import BaseParser
import re


class DatasourceLogicalModelParser(BaseParser):
    """
    Logical Model Parser (REAL TABLES ONLY)
    """

    REAL_DB_CLASSES = {
        "snowflake",
        "postgres",
        "mysql",
        "sqlserver",
        "oracle",
        "redshift",
        "bigquery",
        "teradata"
    }

    def parse(self) -> dict:
        self.log_start()

        tables = []
        seen = set()

        try:
            # ---------------- TIER 1: metadata-records ----------------
            schema_map = {}

            for record in self.root.findall(".//metadata-record[@class='column']"):
                parent = record.findtext("parent-name")
                col = record.findtext("remote-name")
                dtype = record.findtext("local-type") or "unknown"

                if not parent or not col:
                    continue

                table = parent.strip("[]")
                schema_map.setdefault(table, {})
                schema_map[table][col] = dtype

            # ---------------- Parse ONLY REAL datasources ----------------
            for ds in self.root.findall(".//datasource"):

                if not self._is_real_datasource(ds):
                    continue

                ds_name = ds.attrib.get("caption") or ds.attrib.get("name")

                for rel in ds.findall(".//relation[@type='table']"):
                    table_name = rel.attrib.get("name")

                    if not table_name:
                        continue

                    # ❌ Skip extension / internal tables
                    if table_name.lower().startswith("_"):
                        continue
                    if "extension" in table_name.lower():
                        continue

                    key = (ds_name, table_name)
                    if key in seen:
                        continue
                    seen.add(key)

                    columns, source = self._resolve_columns(
                        table_name, schema_map, ds
                    )

                    tables.append({
                        "datasource": ds_name,
                        "table_name": table_name,
                        "relation_type": "table",
                        "schema_source": source,
                        "columns": columns
                    })

            self.log_complete({
                "table_count": len(tables),
                "datasource_count": len({t["datasource"] for t in tables})
            })

            return {"tables": tables}

        except Exception as e:
            self.log_error(e)
            raise

    # ---------------- REAL DATASOURCE CHECK ----------------
    def _is_real_datasource(self, datasource) -> bool:
        for named_conn in datasource.findall(".//named-connection"):
            conn = named_conn.find("./connection")
            if conn is None:
                continue

            cls = (conn.attrib.get("class") or "").lower()
            if cls in self.REAL_DB_CLASSES:
                return True

        return False

    # ---------------- Column Resolution ----------------
    def _resolve_columns(self, table, schema_map, ds):
        if table in schema_map:
            return (
                [{"name": c, "datatype": t} for c, t in schema_map[table].items()],
                "metadata-records"
            )

        cols = {}
        for m in ds.findall(".//cols/map"):
            val = m.attrib.get("value")
            if not val or f"[{table}]." not in val:
                continue

            col = val.split(".")[-1].strip("[]")
            cols[col] = "unknown"

        if cols:
            return (
                [{"name": c, "datatype": t} for c, t in cols.items()],
                "physical-cols-map"
            )

        sql_cols = self._infer_from_custom_sql(ds, table)
        if sql_cols:
            return (
                [{"name": c, "datatype": "unknown"} for c in sql_cols],
                "custom-sql-inferred"
            )

        return [], "unresolved"

    def _infer_from_custom_sql(self, ds, table):
        inferred = set()

        for rel in ds.findall(".//relation[@type='text']"):
            sql = (rel.text or "").lower()
            if "select" not in sql:
                continue

            matches = re.findall(r"\s+as\s+([a-zA-Z0-9_]+)", sql)
            inferred.update(matches)

        return sorted(inferred)
