from app.parsers.base_parser import BaseParser


class PermissionsMetadataParser(BaseParser):

    def parse(self) -> dict:
        self.log_start()

        metadata = {}
        permissions = []

        try:
            workbook = self.root

            # ---------------- METADATA ----------------
            metadata["workbook_id"] = workbook.attrib.get("workbook-id")
            metadata["project_id"] = workbook.attrib.get("project-id")
            metadata["version"] = workbook.attrib.get("version")
            metadata["source_build"] = workbook.attrib.get("source-build")
            metadata["original_version"] = workbook.attrib.get("original-version")
            metadata["locale"] = workbook.attrib.get("locale")
            metadata["show_tabs"] = workbook.attrib.get("show-tabs")

            owner = workbook.find(".//owner")
            if owner is not None:
                metadata["owner"] = {
                    "id": owner.attrib.get("id"),
                    "name": owner.attrib.get("name")
                }
            else:
                metadata["owner"] = None

            # ---------------- PERMISSIONS ----------------
            for perm in workbook.findall(".//permission"):
                grantee = perm.find("grantee")
                capabilities = []

                for cap in perm.findall(".//capability"):
                    capabilities.append({
                        "name": cap.attrib.get("name"),
                        "mode": cap.attrib.get("mode")
                    })

                permissions.append({
                    "grantee_type": grantee.attrib.get("type") if grantee is not None else None,
                    "grantee_name": grantee.attrib.get("name") if grantee is not None else None,
                    "capabilities": capabilities
                })

            self.log_complete({
                "permission_entry_count": len(permissions)
            })

            return {
                "metadata": metadata,
                "permissions": permissions
            }

        except Exception as e:
            self.log_error(e)
            raise
