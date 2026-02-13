import os
from abc import ABC, abstractmethod
from app.core.config import settings
from app.utils.xml_loader import TableauXMLLoader


class WorkbookResolver(ABC):
    @abstractmethod
    def resolve(self, project_id: str, workbook_id: str) -> str:
        pass


class LocalWorkbookResolver(WorkbookResolver):

    def resolve(self, project_id: str, workbook_id: str) -> str:
        root_dir = settings.STORAGE_ROOT
        print(f"[DEBUG] STORAGE_ROOT = {root_dir}")

        for dirpath, _, files in os.walk(root_dir):
            for file in files:
                if not (file.endswith(".twb") or file.endswith(".xml")):
                    continue
                
                path = os.path.join(dirpath, file)
                print(f"[DEBUG] Checking file: {path}")

                try:
                    xml_root = TableauXMLLoader.load(path)

                    xml_project_id = xml_root.attrib.get("project-id")
                    xml_workbook_id = xml_root.attrib.get("workbook-id")

                    print(f"[DEBUG] XML project-id  = {xml_project_id}")
                    print(f"[DEBUG] XML workbook-id = {xml_workbook_id}")

                    if (
                        xml_project_id == project_id
                        and xml_workbook_id == workbook_id
                    ):
                        print("[DEBUG] MATCH FOUND")
                        return path

                except Exception as e:
                    print(f"[DEBUG] Failed to parse {path}: {e}")
                    continue

        raise FileNotFoundError("Workbook not found for given IDs")
