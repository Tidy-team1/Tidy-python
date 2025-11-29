from pydantic import BaseModel

class IssueElement(BaseModel):
    shapeId: int | None = None
    elementIndex: int | None = None
    bboxLeft: int | None = None
    bboxTop: int | None = None
    bboxWidth: int | None = None
    bboxHeight: int | None = None
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
