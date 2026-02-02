
import os
from app.parsers.base_parser import BaseParser


class EmbeddedAssetsParser(BaseParser):

    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

    def __init__(self, root, context, workspace_path=None):
        super().__init__(root, context)
        self.workspace_path = workspace_path

    def parse(self) -> dict:
        images = []
        web_assets = []

        # XML web assets
        for url in self.root.findall(".//url"):
            if url.text:
                web_assets.append({"value": url.text})

        # ✅ ABSOLUTE PATH WALK
        if self.workspace_path and os.path.exists(self.workspace_path):
            for root_dir, _, files in os.walk(self.workspace_path):
                for f in files:
                    if f.lower().endswith(self.IMAGE_EXTENSIONS):
                        file_path = os.path.join(root_dir, f)

                        images.append({
                            "name": f,
                            "source": "workspace",
                            "embedded": True,
                            "relative_path": os.path.relpath(
                                file_path, self.workspace_path
                            ),
                            "size_kb": round(os.path.getsize(file_path) / 1024, 2)
                        })

        return {
            "images": images,
            "shapes": [],
            "backgrounds": [],
            # "hyper_previews": [],
            "web_assets": web_assets
        }


