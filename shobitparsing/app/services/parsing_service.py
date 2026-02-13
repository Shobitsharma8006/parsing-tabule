import shutil
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from azure.storage.blob import BlobServiceClient

from app.extractors.twbx_extractor import TwbxExtractor
from app.core.config import settings
from app.services.mongo_writer_service import MongoWriterService

# Specialized Parsers
from app.parsers.workbook_parser import WorkbookParser
from app.parsers.datasource_parser import DatasourceParser
from app.parsers.calculation_parser import CalculationParser
from app.parsers.extract_parser import ExtractParser
from app.parsers.security_parser import SecurityParser
from app.parsers.parameter_set_parser import ParameterSetParser
from app.parsers.sheet_visual_parser import SheetVisualParser
from app.parsers.dashboard_story_parser import DashboardStoryParser
from app.parsers.formatting_parser import FormattingParser
from app.parsers.embedded_assets_parser import EmbeddedAssetsParser
from app.parsers.permissions_metadata_parser import PermissionsMetadataParser
from app.parsers.action_parser import ActionParser
from app.parsers.filter_parser import FilterParser

class ParsingService:
    def __init__(self):
        # Azure Storage Setup
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_client = self.blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )
        # Database Writer Setup
        self.mongo_writer = MongoWriterService()

    def _fetch_from_azure(self, run_id: str, workbook_id: str) -> str:
        """Downloads the .twbx file from projects/{run_id}/{workbook_id}/"""
        prefix = f"projects/{run_id}/{workbook_id}/"
        print(f"[INFO] Searching Azure for: {prefix}")
        
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        target_blob = None
        for blob in blobs:
            if blob.name.lower().endswith(".twbx"):
                target_blob = blob.name
                break
        
        if not target_blob:
            raise FileNotFoundError(f"No .twbx file found in Azure path: {prefix}")

        local_path = os.path.join(settings.WORKSPACE_ROOT, os.path.basename(target_blob))
        os.makedirs(settings.WORKSPACE_ROOT, exist_ok=True)

        with open(local_path, "wb") as f:
            data = self.container_client.download_blob(target_blob)
            f.write(data.readall())
        
        print(f"[INFO] Downloaded: {os.path.basename(target_blob)}")
        return local_path

    def parse(self, run_id: str, workbook_id: str) -> dict:
        """Executes full workflow: Download -> Extract -> Parse All -> Save to DB"""
        context = {"run_id": run_id, "workbook_id": workbook_id}
        
        # 1. Retrieval
        twbx_path = self._fetch_from_azure(run_id, workbook_id)

        # 2. Extraction & Validation (Converts TWBX to TWB XML and extracts assets)
        extracted = TwbxExtractor.extract(twbx_path, settings.WORKSPACE_ROOT)

        try:
            # 3. Load XML
            tree = ET.parse(extracted["twb_path"])
            root = tree.getroot()

            # 4. Comprehensive Parsing
            action_data = ActionParser(root, context).parse()
            
            # This result object contains everything: Datasources, LODs, Visuals, etc.
            result_data = {
                "metadata": {
                    "run_id": run_id,
                    "workbook_id": workbook_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "file_info": WorkbookParser(root, context).parse(),
                    "permissions": PermissionsMetadataParser(root, context).parse(),
                    "filters": FilterParser(root, context).parse()
                },
                "datasources_and_connections": DatasourceParser(root, context).parse(),
                "calculations_and_lods": CalculationParser(root, context).parse(),
                "parameters_and_sets": ParameterSetParser(root, context).parse(),
                "sheets_and_visuals": SheetVisualParser(root, context).parse(),
                "dashboards_and_stories": DashboardStoryParser(root, context).parse(),
                "actions": action_data.get("actions", []),
                "highlights": action_data.get("highlights", []),
                "formatting_and_styling": FormattingParser(root, context).parse(),
                "embedded_assets": {
                    "images_and_shapes": EmbeddedAssetsParser(
                        root, context, workspace_path=extracted["workspace_path"]
                    ).parse(),
                    "extracts": ExtractParser(root, context).parse(),
                },
                "security": SecurityParser(root, context).parse(),
                "artifacts": {
                    "twbx_source": os.path.basename(twbx_path),
                    "hyper_files": extracted["hyper_paths"]
                }
            }

            # 5. Store result in MongoDB via the API endpoint
            self.mongo_writer.write_result(result_data)

            return result_data

        finally:
            # 6. Cleanup local files
            shutil.rmtree(extracted["workspace_path"], ignore_errors=True)
            if os.path.exists(twbx_path):
                os.remove(twbx_path)