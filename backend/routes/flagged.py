from fastapi import APIRouter

from storage.memory_store import memory_store
from schemas.response import FlaggedRecordsResponse

router = APIRouter()


@router.get(
    "/flagged-records",
    response_model=FlaggedRecordsResponse,
)
def get_flagged_records():
    """
    Returns all flagged records
    from the latest analysis.
    """

    records = memory_store.get_records()

    return FlaggedRecordsResponse(
        records=records
    )