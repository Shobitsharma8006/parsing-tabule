from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xml.etree.ElementTree as ET
import os
import uuid

# Configuration and Extractor
from app.core.config import settings
from app.extractors.twbx_extractor import TwbxExtractor

# Services
from app.services.agent_logger import send_log_to_api
from app.services.mongo_writer_service import store_parsing_result_to_mongo

# Base + Parsers
from app.parsers.base_parser import BaseParser
from app.parsers.workbook_parser import WorkbookParser
from app.parsers.datasource_parser import DatasourceParser
from app.parsers.datasource_logical_model_parser import DatasourceLogicalModelParser
from app.parsers.datasource_relationship_parser import DatasourceRelationshipParser
from app.parsers.measure_parser import MeasureParser
from app.parsers.calculation_parser import CalculationParser
from app.parsers.extract_parser import ExtractParser
from app.parsers.security_parser import SecurityParser
from app.parsers.parameter_set_parser import ParameterSetParser
from app.parsers.schema_parser import SchemaParser
from app.parsers.sheet_visual_parser import SheetVisualParser
from app.parsers.dashboard_story_parser import DashboardStoryParser
from app.parsers.action_parser import ActionParser
from app.parsers.formatting_parser import FormattingParser
from app.parsers.permissions_metadata_parser import PermissionsMetadataParser
from app.parsers.embedded_assets_parser import EmbeddedAssetsParser
from app.parsers.filter_parser import FilterParser

from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------
# FastAPI setup
# -------------------------------------------------
app = FastAPI(title="Tableau XML Metadata API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Request Model
# -------------------------------------------------
class ParseRequest(BaseModel):
    project_id: str
    workbook_id: str
    run_id: str


# -------------------------------------------------
# API
# -------------------------------------------------
@app.post("/parse-xml")
async def parse_xml(req: ParseRequest):
    BaseParser.init_sequence()
    run_id = str(uuid.uuid4())

    # -------------------------------------------------
    # 1️⃣ Locate workbook file
    # -------------------------------------------------
    twbx_filename = "City hospital 2  (1).twbx"

    twbx_path = os.path.join(
        settings.STORAGE_ROOT,
        "uploaded",
        twbx_filename
    )

    if not os.path.exists(twbx_path):
        raise HTTPException(
            status_code=404,
            detail=f"Workbook file not found at {twbx_path}"
        )

    file_type = "twbx" if twbx_path.lower().endswith(".twbx") else "twb"

    try:
        # -------------------------------------------------
        # 2️⃣ Extract workbook
        # -------------------------------------------------
        extraction = TwbxExtractor.extract(
            twbx_path=twbx_path,
            workspace_root="app/extractors/workspaces"
        )

        workspace_path = extraction["workspace_path"]

        # -------------------------------------------------
        # 3️⃣ Load TWB XML
        # -------------------------------------------------
        tree = ET.parse(extraction["twb_path"])
        matched_root = tree.getroot()

        await send_log_to_api(
            req.project_id,
            req.workbook_id,
            run_id,
            "INFO",
            "Unzipping completed, parsing started"
        )

        # -------------------------------------------------
        # 4️⃣ Shared Context (🔥 THIS CONTROLS EVERYTHING)
        # -------------------------------------------------
        context = {
            "project_id": req.project_id,
            "workbook_id": req.workbook_id,
            "run_id": run_id,
            "workspace_path": workspace_path,
            "file_type": file_type
        }

        # -------------------------------------------------
        # 5️⃣ Execute Parsers (ORDER IS CRITICAL)
        # -------------------------------------------------

        # Measures
        measures = MeasureParser(matched_root, context).parse()
        context["measures"] = measures

        # Calculations
        calc_result = CalculationParser(matched_root, context).parse()

        # ✅ ACTIONS MUST BE PARSED BEFORE DASHBOARDS/STORIES
        actions_result = ActionParser(matched_root, context).parse()
        context["actions"] = actions_result   # 🔥 THIS LINE ENABLES ACTIONS

        # -------------------------------------------------
        # 6️⃣ Build final response
        # -------------------------------------------------
        parsing_result = {
            "run_id": run_id,
            "file_type": file_type,

            "workbook": WorkbookParser(matched_root, context).parse(),

            "datasources": DatasourceParser(matched_root, context).parse(),

            "logical_model": DatasourceLogicalModelParser(
                matched_root, context
            ).parse(),

            "joins": DatasourceRelationshipParser(
                matched_root, context
            ).parse(),

            "calculations": {
                "measures": measures,
                "calculated_fields": calc_result.get("calculated_fields", {}),
                "lod_expressions": calc_result.get("lod_expressions", {}),
                "filters": calc_result.get("filters", {})
            },

            "parameters_sets": ParameterSetParser(
                matched_root, context
            ).parse(),

            "schema": SchemaParser(matched_root, context).parse(),

            "sheets_visuals": SheetVisualParser(
                matched_root, context
            ).parse(),

            # ✅ DASHBOARDS + STORIES NOW SEE ACTIONS
            "dashboards_stories": DashboardStoryParser(
                matched_root, context
            ).parse(),

            "filters": FilterParser(matched_root, context).parse(),

            # Optional global view
            "actions": actions_result,

            "formatting_and_styling": FormattingParser(
                matched_root, context
            ).parse(),

            "permissions_metadata": PermissionsMetadataParser(
                matched_root, context
            ).parse(),

            "embedded_assets": EmbeddedAssetsParser(
                matched_root,
                context,
                workspace_path=workspace_path
            ).parse(),

            "extracts": ExtractParser(matched_root, context).parse(),

            "security": SecurityParser(matched_root, context).parse()
        }

        # -------------------------------------------------
        # 7️⃣ Store result
        # -------------------------------------------------
        store_parsing_result_to_mongo(parsing_result)

        await send_log_to_api(
            req.project_id,
            req.workbook_id,
            run_id,
            "INFO",
            "Parsing completed and stored",
            {"sections": list(parsing_result.keys())}
        )

        return {
            "message": "Parsing completed successfully",
            "workspace": workspace_path,
            **parsing_result
        }

    except Exception as e:
        await send_log_to_api(
            req.project_id,
            req.workbook_id,
            run_id,
            "ERROR",
            "Process failed",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
