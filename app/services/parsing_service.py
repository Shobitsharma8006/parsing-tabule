import shutil
import os
import xml.etree.ElementTree as ET

from app.extractors.twbx_extractor import TwbxExtractor
from app.core.config import settings

# XML parsers
from app.parsers.workbook_parser import WorkbookParser
from app.parsers.datasource_parser import DatasourceParser
from app.parsers.calculation_parser import CalculationParser
from app.parsers.extract_parser import ExtractParser
from app.parsers.security_parser import SecurityParser
from app.parsers.schema_parser import SchemaParser
# (later: parameters, sets, visuals, actions, dashboards)


class ParsingService:

    def parse(self, project_id: str, workbook_id: str) -> dict:

        # -------------------------------------------------
        # STEP 1: Validate storage
        # -------------------------------------------------
        if not os.path.exists(settings.STORAGE_ROOT):
            raise FileNotFoundError(f"STORAGE_ROOT not found: {settings.STORAGE_ROOT}")

        twbx_files = [
            f for f in os.listdir(settings.STORAGE_ROOT)
            if f.endswith(".twbx")
        ]
        if not twbx_files:
            raise FileNotFoundError("No TWBX files found")

        twbx_path = os.path.join(settings.STORAGE_ROOT, twbx_files[0])

        # -------------------------------------------------
        # STEP 2: Extract TWBX
        # -------------------------------------------------
        extracted = TwbxExtractor.extract(
            twbx_path=twbx_path,
            workspace_root=settings.WORKSPACE_ROOT
        )

        try:
            # -------------------------------------------------
            # STEP 3: Load TWB (XML)
            # -------------------------------------------------
            twb_path = extracted["twb_path"]
            tree = ET.parse(twb_path)
            root = tree.getroot()

            # -------------------------------------------------
            # STEP 4: Run XML parsers
            # -------------------------------------------------
            workbook = WorkbookParser(root).parse()
            datasources = DatasourceParser(root).parse()
            calculations = CalculationParser(root).parse()
            extracts = ExtractParser(root).parse()
            security = SecurityParser(root).parse()
            schema = SchemaParser(root).parse()

            # -------------------------------------------------
            # STEP 5: Build response (incremental)
            # -------------------------------------------------
            return {
                "project_id": project_id,
                "workbook_id": workbook_id,

                "workbook": workbook,
                "datasources": datasources,
                "calculations": calculations,
                "schema": schema,
                "extracts": extracts,
                "security": security,

                # raw paths (useful for debugging)
                "artifacts": {
                    "twbx": twbx_path,
                    "twb": twb_path,
                    "hyper_files": extracted["hyper_paths"]
                }
            }

        finally:
            # -------------------------------------------------
            # STEP 6: Cleanup workspace
            # -------------------------------------------------
            shutil.rmtree(extracted["workspace_path"], ignore_errors=True)
