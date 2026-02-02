from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.parsing_service import ParsingService


router = APIRouter()
service = ParsingService()

class ParseRequest(BaseModel):
    project_id: str
    workbook_id: str

@router.post("/parse")
def parse(req: ParseRequest):
    try:
        return service.parse(req.project_id, req.workbook_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    
