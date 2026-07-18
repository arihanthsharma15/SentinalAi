from typing import List
from pydantic import BaseModel, Field



class GemmaAnalysis(BaseModel):
    risk_score: int
    risk_category: str
    explanation: str
    recommended_action: str


class FlaggedRecord(BaseModel):
    id: str
    type: str


    sender: str
    receiver: str

    amount: float

    rules_triggered: List[str]

    gemmaAnalysis: GemmaAnalysis


class FlaggedRecordsResponse(BaseModel):
    records: List[FlaggedRecord] = Field(default_factory=list)