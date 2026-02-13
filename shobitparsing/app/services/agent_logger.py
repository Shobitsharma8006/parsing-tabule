import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings  # wherever MONGO_API_URL lives

logger = logging.getLogger(__name__)


async def send_log_to_api(
    project_id: str,
    workbook_id: str,
    run_id: str,
    log_level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    base_url = settings.mongo_api_url
    if not base_url:
        return

    api_url = f"{base_url.rstrip('/')}/api/records/logs"

    payload = {
        "project_name": project_id,
        "project_id": project_id,
        "workbook_id": workbook_id,
        "run_id": run_id,
        "agent_name": "Parsing Agent",
        "log_level": log_level.upper(),
        "message": message,
        "details": details or {}
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(api_url, json=payload)
    except Exception as e:
        logger.error(f"[Parsing Agent Logging Failed] {e}")
