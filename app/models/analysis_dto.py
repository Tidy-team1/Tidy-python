from pydantic import BaseModel

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


class ReviewAnalysisResult(BaseModel):
    results: list[SlideIssueResult]
