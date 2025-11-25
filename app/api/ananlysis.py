from fastapi import APIRouter
from pydantic import BaseModel
from app.services.review_analysis_service import analyze_review
from app.core.logger import logger

router = APIRouter(prefix="/analysis")


class ReviewAnalysisRequest(BaseModel):
    spaceId: int
    presentationId: int
    options: list[str]

@router.post("/review")
def review_analysis(req: ReviewAnalysisRequest):
    result = analyze_review(
        space_id=req.spaceId,
        presentation_id=req.presentationId,
        options=req.options
    )
    return {"result": result}

