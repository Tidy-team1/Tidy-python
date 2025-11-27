from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ppt_parser_service import parse_ppt

router = APIRouter(prefix="/parsing")

class ParseRequest(BaseModel):
    spaceId: int
    presentationId: int

@router.post("/parse")
def parse(req: ParseRequest):
    return parse_ppt(req.spaceId, req.presentationId)
