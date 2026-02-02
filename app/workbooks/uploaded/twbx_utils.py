import os
import zipfile
import shutil
import uuid

def unzip_twbx(twbx_path: str) -> dict:
    if not os.path.exists(twbx_path):
        raise FileNotFoundError(f"TWBX not found: {twbx_path}")

    run_id = str(uuid.uuid4())

    base_dir = os.path.join(
        "app", "workbooks", "extracted", run_id
    )
    os.makedirs(base_dir, exist_ok=True)

    with zipfile.ZipFile(twbx_path, "r") as zip_ref:
        zip_ref.extractall(base_dir)

    # find the workbook xml
    workbook_xml = None
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".twb"):
                workbook_xml = os.path.join(root, f)
                break

    if not workbook_xml:
        raise RuntimeError("No .twb file found inside TWBX")

    return {
        "run_id": run_id,
        "extracted_dir": base_dir,
        "workbook_xml": workbook_xml
    }
