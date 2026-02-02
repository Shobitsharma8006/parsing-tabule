



from app.parsers.base_parser import BaseParser


class DatasourceParser(BaseParser):

    def parse(self) -> dict:
        self.log_start()

        datasources = []
        seen_ids = set()

        try:
            for ds in self.root.findall("./datasources/datasource"):

                # Skip non-real datasources
                if not self._is_actual_datasource(ds):
                    continue

                ds_id = ds.attrib.get("name")
                if ds_id in seen_ids:
                    continue
                seen_ids.add(ds_id)

                ds_name = ds.attrib.get("caption") or ds_id
                inline = ds.attrib.get("inline") == "true"

                connections = []
                files = []
                embedded_credentials = []

                has_live_db = False
                connection_type = None

                # -------------------------------------------------
                # CONNECTIONS + EMBEDDED CREDENTIALS
                # -------------------------------------------------
                for named_conn in ds.findall(".//named-connection"):
                    conn = named_conn.find("./connection")
                    if conn is None:
                        continue

                    cls = conn.attrib.get("class")

                    # Ignore Tableau internal extract connections
                    if cls in ("hyper", "textscan"):
                        continue

                    has_live_db = True
                    connection_type = conn.attrib.get("dbname")

                    # -------- CONNECTION DETAILS --------
                    connections.append({
                        "friendly_name": named_conn.attrib.get("caption"),
                        "type": cls,
                        "server": conn.attrib.get("server"),
                        "warehouse": conn.attrib.get("warehouse"),
                        "database": conn.attrib.get("dbname"),
                        "schema": conn.attrib.get("schema"),
                        "username": conn.attrib.get("username"),
                        "service": conn.attrib.get("service"),
                        "port": conn.attrib.get("port"),
                    })

                    # -------- EMBEDDED CREDENTIALS --------
                    embed_pwd = conn.attrib.get("embedpassword") == "true"
                    username = conn.attrib.get("username")
                    auth_type = conn.attrib.get("authentication")
                    oauth = conn.attrib.get("oauth") == "true"

                    if embed_pwd or oauth:
                        embedded_credentials.append({
                            "username": username,
                            "auth_type": auth_type or ("oauth" if oauth else None),
                            "embedded": embed_pwd,
                            "oauth": oauth
                        })

                # -------------------------------------------------
                # FILE-BASED EXTRACTS
                # -------------------------------------------------
                for conn in ds.findall(".//connection"):
                    cls = conn.attrib.get("class")
                    if cls == "textscan":
                        files.append("CSV")
                    elif cls in ("excel", "excel-direct"):
                        files.append("Excel")
                    elif cls == "google-drive":
                        files.append("Google Sheets")

                mode = "live" if has_live_db else "extract"

                datasources.append({
                    "id": ds_id,
                    "name": ds_name,
                    "inline": inline,
                    "mode": mode,
                    "connection_type": connection_type if mode == "live" else None,
                    "connections": connections if mode == "live" else [],
                    "files": list(set(files)) if mode == "extract" else [],
                    "embedded_credentials": embedded_credentials
                })

            self.log_complete({"datasource_count": len(datasources)})
            return {"datasources": datasources}

        except Exception as e:
            self.log_error(e)
            raise

    # ==================================================
    # FILTER: ONLY REAL DATASOURCES
    # ==================================================
    def _is_actual_datasource(self, datasource) -> bool:
        ds_name = (datasource.attrib.get("name") or "").lower()

        if ds_name == "parameters":
            return False

        if "spatial" in ds_name or "analytics" in ds_name:
            return False

        connections = datasource.findall(".//connection")
        return bool(connections)
