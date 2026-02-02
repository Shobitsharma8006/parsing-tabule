


from app.parsers.base_parser import BaseParser

class WorkbookParser(BaseParser):
    def parse(self) -> dict:
        self.log_start()

        try:
            repo = self.root.find(".//repository-location")

            technical_name = None
            display_name = None

            if repo is not None:
                technical_name = repo.attrib.get("id")
                display_name = repo.attrib.get("name")

            if not display_name:
                display_name = (
                    technical_name.replace("_", " ").title()
                    if technical_name else None
                )

            # ✅ ADD THIS BLOCK
            workspace_id = self.context.get("workbook_id")
            workspace_path = f"app/extractors/workspaces/{workspace_id}"
            self.context["workspace_path"] = workspace_path
            # ✅ END

            result = {
                "technical_name": technical_name,
                "display_name": display_name,
                "project_id": self.context["project_id"],
                "workbook_id": self.context["workbook_id"],
                "version": self.root.attrib.get("version"),
                "source_build": self.root.attrib.get("source-build"),
                "original_version": self.root.attrib.get("original-version"),
            }

            self.log_complete()
            return result

        except Exception as e:
            self.log_error(e)
            raise
