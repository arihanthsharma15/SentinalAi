from pydantic import BaseModel


class AnalysisReport(BaseModel):
    transaction_filename: str
    invoice_filename: str