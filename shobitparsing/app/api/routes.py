from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.parsing_service import ParsingService

router = APIRouter()
service = ParsingService()

class ParseRequest(BaseModel):
    run_id: str
    workbook_id: str

@router.post("/parse")
def parse(req: ParseRequest):
    try:
        return service.parse(req.run_id, req.workbook_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")