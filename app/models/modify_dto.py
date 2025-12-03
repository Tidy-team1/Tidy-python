from pydantic import BaseModel
from typing import List, Optional


class ApplyFeedbackPayload(BaseModel):
    presentationId: int
    slideIndex: int

    type: str               # "font_consistency" 등
    detailsJson: str        # raw JSON string

    shapeId: Optional[int]
    elementIndex: Optional[int]

    bboxLeft: float
    bboxTop: float
    bboxWidth: float
    bboxHeight: float


class ApplyFeedbackBatchPayload(BaseModel):
    spaceId: int
    presentationId: int

    baseVersion: int
    targetVersion: int

    items: List[ApplyFeedbackPayload]
