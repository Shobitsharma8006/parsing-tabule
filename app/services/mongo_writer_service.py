import uuid
import requests
from typing import Dict, Any


def store_parsing_result_to_mongo(
    parsing_result: Dict[str, Any],
    mongo_api_url: str = os.environ.get("MONGO_API_URL", "")+"/api/records/parsing",
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Stores parsed Tableau metadata JSON into MongoDB via REST API.
    """

    workbook = parsing_result.get("workbook", {})

    project_id = workbook.get("project_id")
    workbook_id = workbook.get("workbook_id")
    project_name = workbook.get("display_name")

    if not all([project_id, workbook_id]):
        raise ValueError(
            "Parsing result missing required workbook identifiers "
            "(project_id / workbook_id)"
        )

    payload = {
        # 🔑 REQUIRED BY MONGO API (TOP LEVEL)
        "project_id": project_id,
        "workbook_id": workbook_id,
        "project_name": project_name,

        # 🔁 Run tracking
        "run_id": parsing_result.get("run_id") or str(uuid.uuid4()),
        "status": "parsed",

        # 📦 Full parsing payload (unchanged)
        "payload": parsing_result
    }

    response = requests.post(
        mongo_api_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=timeout
    )

    if not response.ok:
        raise RuntimeError(
            f"Mongo API failed | "
            f"Status: {response.status_code} | "
            f"Response: {response.text}"
        )

    return response.json()
