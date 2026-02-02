from abc import ABC, abstractmethod

class StorageResolver(ABC):
    @abstractmethod
    def resolve(self, project_id: str, workbook_id: str) -> str:
        pass


import os
from app.core.config import settings

class LocalStorageResolver(StorageResolver):
    def resolve(self, project_id: str, workbook_id: str) -> str:
        for file in os.listdir(settings.STORAGE_ROOT):
            if file.endswith(".twbx"):
                if project_id in file and workbook_id in file:
                    return os.path.join(settings.STORAGE_ROOT, file)

        raise FileNotFoundError("TWBX not found")
