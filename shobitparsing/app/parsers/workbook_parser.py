from app.parsers.base_parser import BaseParser

class WorkbookParser(BaseParser):
    def parse(self) -> dict:
        """
        Parses workbook-level metadata. 
        Safely retrieves attributes to prevent KeyError in local workbooks.
        """
        # Find repository location for accurate name and site info
        repo_loc = self.root.find(".//repository-location")
        
        return {
            "name": repo_loc.attrib.get("id", "Unknown") if repo_loc is not None else "Unknown",
            "version": self.root.attrib.get("version", "18.1"),
            "source_build": self.root.attrib.get("source-build", ""),
            "site": repo_loc.attrib.get("site", "") if repo_loc is not None else "",
            # Compatibility fields for legacy logic
            "project_id": self.root.attrib.get("project-id", ""),
            "workbook_id": self.root.attrib.get("workbook-id", "")
        }