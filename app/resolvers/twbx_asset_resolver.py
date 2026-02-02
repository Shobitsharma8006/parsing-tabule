import zipfile
import os
from typing import Dict, List


class TwbxAssetResolver:
    """
    Resolves embedded assets from a TWBX file.
    Responsible ONLY for extraction & mapping.
    """

    ASSET_DIRS = ["Images", "Shapes", "Backgrounds", "thumbnails"]

    @staticmethod
    def extract_twbx(twbx_path: str, workspace_root: str) -> str:
        """
        Unzips the TWBX into a workspace directory.
        Returns the extraction root.
        """
        if not zipfile.is_zipfile(twbx_path):
            raise ValueError("Provided file is not a valid TWBX")

        workbook_id = os.path.splitext(os.path.basename(twbx_path))[0]
        extract_root = os.path.join(workspace_root, "twbx", workbook_id, "extracted")

        os.makedirs(extract_root, exist_ok=True)

        with zipfile.ZipFile(twbx_path, "r") as zf:
            zf.extractall(extract_root)

        return extract_root

    @staticmethod
    def resolve_assets(extract_root: str) -> Dict[str, List[Dict]]:
        """
        Scans extracted TWBX directories and returns asset metadata.
        """
        assets = {
            "images": [],
            "shapes": [],
            "backgrounds": [],
            "thumbnails": []
        }

        for root, dirs, files in os.walk(extract_root):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_root)

                if "Images" in rel_path:
                    assets["images"].append(TwbxAssetResolver._asset(file, rel_path))
                elif "Shapes" in rel_path:
                    assets["shapes"].append(TwbxAssetResolver._asset(file, rel_path))
                elif "Backgrounds" in rel_path:
                    assets["backgrounds"].append(TwbxAssetResolver._asset(file, rel_path))
                elif "thumbnails" in rel_path.lower():
                    assets["thumbnails"].append(TwbxAssetResolver._asset(file, rel_path))

        return assets

    @staticmethod
    def _asset(name: str, path: str) -> Dict:
        return {
            "name": name,
            "path": path,
            "extension": os.path.splitext(name)[1].lower()
        }
