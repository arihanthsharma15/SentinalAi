from pydantic import BaseModel


class Transaction(BaseModel):
    transaction_id: str
    sender_name: str
    sender_account_age_days: int
    receiver_name: str
    receiver_account_age_days: int
    amount: float
    timestamp: str
    transaction_type: str
    location: str
    description: str
    linked_invoice_id: str | None = None