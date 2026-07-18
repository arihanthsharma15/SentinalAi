from pydantic import BaseModel


class Invoice(BaseModel):
    invoice_id: str
    vendor_name: str
    gst_number: str
    amount: float
    invoice_date: str
    payment_status: str
    linked_transaction_id: str | None = None