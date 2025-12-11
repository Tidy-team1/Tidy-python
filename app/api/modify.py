from fastapi import APIRouter, HTTPException
from app.models.modify_dto import ApplyFeedbackBatchPayload
from app.services.modify.service import process_modify

router = APIRouter()


@router.post("/modify")
async def modify(batch: ApplyFeedbackBatchPayload):
    result = process_modify(batch)
    return result