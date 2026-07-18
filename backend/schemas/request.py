from pydantic import BaseModel


class AnalysisRequet(BaseModel):
    transaction_filename: str
    invoice_filename: str