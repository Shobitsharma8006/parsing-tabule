import os
import requests
import logging

logger = logging.getLogger(__name__)

class MongoWriterService:
    def __init__(self):
        # Default to localhost if environment variable is not set
        self.base_url = os.environ.get("MONGO_API_URL", "http://localhost:3000")
        self.endpoint = f"{self.base_url}/api/records/parsing"

    def write_result(self, result_data: dict):
        """
        Sends the parsed data to the @router.post("/parsing") endpoint.
        Matches the payload structure you provided.
        """
        payload = {
            "run_id": result_data.get("metadata", {}).get("run_id", "Unknown"),
            "project_id": result_data.get("metadata", {}).get("run_id", "Unknown"), # Using run_id as project identifier
            "workbook_id": result_data.get("metadata", {}).get("workbook_id", "Unknown"),
            "project_name": result_data.get("metadata", {}).get("file_info", {}).get("name", "Unknown"),
            "status": "completed",
            "payload": result_data
        }
        
        try:
            print(f"[INFO] Sending payload to database: {self.endpoint}")
            response = requests.post(self.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            logger.info("Successfully stored parsing results in MongoDB.")
            return response.json()
        except Exception as e:
            logger.error(f"Database Storage Failed: {str(e)}")
            return None