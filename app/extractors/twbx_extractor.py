import zipfile
import os
import uuid
import shutil

class TwbxExtractor:
    @staticmethod
    def extract(twbx_path: str, workspace_root: str) -> dict:
        """
        Extracts a TWBX file into a unique workspace.
        Returns paths to TWB and Hyper files.
        """

        # Create isolated workspace
        workspace_id = str(uuid.uuid4())
        workspace_path = os.path.join(workspace_root, workspace_id)
        os.makedirs(workspace_path, exist_ok=True)

        # Unzip TWBX
        with zipfile.ZipFile(twbx_path, "r") as zip_ref:
            zip_ref.extractall(workspace_path)

        twb_path = None
        hyper_paths = []

        # Discover contents
        for root, _, files in os.walk(workspace_path):
            for file in files:
                if file.endswith(".twb"):
                    twb_path = os.path.join(root, file)
                elif file.endswith(".hyper"):
                    hyper_paths.append(os.path.join(root, file))

        if not twb_path:
            shutil.rmtree(workspace_path)
            raise ValueError("No .twb file found inside TWBX")

        return {
            "workspace_path": workspace_path,
            "twb_path": twb_path,
            "hyper_paths": hyper_paths
        }
