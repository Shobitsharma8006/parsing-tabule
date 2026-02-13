# app/resolvers/storage_resolver.py
from azure.storage.blob import BlobServiceClient
from app.core.config import settings
import os

class AzureStorageResolver(StorageResolver):
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_client = self.blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )

    def resolve(self, project_id: str, workbook_id: str) -> str:
        # Construct the prefix based on your folder structure: project_id/workbook_id/
        prefix = f"{project_id}/{workbook_id}/"
        
        # List blobs in that specific "folder"
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        
        for blob in blobs:
            if blob.name.endswith(".twbx"):
                # Download to a temporary location in your WORKSPACE_ROOT
                download_path = os.path.join(settings.WORKSPACE_ROOT, os.path.basename(blob.name))
                
                with open(download_path, "wb") as file:
                    blob_data = self.container_client.download_blob(blob.name)
                    file.write(blob_data.readall())
                
                return download_path

        raise FileNotFoundError(f"TWBX not found in Azure path: {prefix}")