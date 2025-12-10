from pydantic import BaseModel
from typing import List, Optional, Dict, Any # import문 추가

class IssueElement(BaseModel):
    shapeId: int | None = None
    elementIndex: int | None = None
    bboxLeft: float | None = None
    bboxTop: float | None = None
    bboxWidth: float | None = None
    bboxHeight: float | None = None
    text: str | None = None
    elementType: str | None = None


class IssueResult(BaseModel):
    type: str
    message: str
    element: IssueElement
    details: dict


class SlideIssueResult(BaseModel):
    slide: int
    issues: list[IssueResult]

    # 점수 관련 필드 추가
    readability_score: Optional[float] = None
    aesthetic_score: Optional[float] = None 
    consistency_score: Optional[float] = None

class ReviewAnalysisResult(BaseModel):
    results: list[SlideIssueResult]
