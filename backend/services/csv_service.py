from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile

from models.transaction import Transaction
from models.invoice import Invoice


class CSVService:
    """
    Handles:
    - CSV validation
    - CSV parsing
    - Conversion to Pydantic models
    """

    REQUIRED_TRANSACTION_COLUMNS = {
        "transaction_id",
        "sender_name",
        "sender_account_age_days",
        "receiver_name",
        "receiver_account_age_days",
        "amount",
        "timestamp",
        "transaction_type",
        "location",
        "description",
        "linked_invoice_id",
    }

    REQUIRED_INVOICE_COLUMNS = {
        "invoice_id",
        "vendor_name",
        "gst_number",
        "amount",
        "invoice_date",
        "payment_status",
        "linked_transaction_id",
    }

    @staticmethod
    async def save_upload(upload_file: UploadFile, destination: Path) -> Path:
        """
        Save uploaded CSV to disk and return the saved path.
        """

        destination.parent.mkdir(parents=True, exist_ok=True)

        contents = await upload_file.read()

        with open(destination, "wb") as file:
            file.write(contents)

        return destination

    @staticmethod
    def validate_columns(df: pd.DataFrame, required_columns: set):
        """
        Ensure CSV contains all required columns.
        """

        missing = required_columns - set(df.columns)

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(sorted(missing))}"
            )

    @staticmethod
    def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Map the shipped transaction CSV schema to the backend model fields.
        """

        normalized = df.copy()

        if "location" not in normalized.columns:
            location = normalized.get("city", pd.Series([""] * len(normalized))).fillna("").astype(str)

            for column in ("state", "country"):
                if column in normalized.columns:
                    location = location + ", " + normalized[column].fillna("").astype(str)

            normalized["location"] = location.str.strip(", ")

        if "description" not in normalized.columns:
            normalized["description"] = normalized.get(
                "remarks",
                "",
            ).fillna("")

        if "receiver_account_age_days" not in normalized.columns:
            normalized["receiver_account_age_days"] = normalized.get(
                "sender_account_age_days",
                0,
            )

        if "linked_invoice_id" not in normalized.columns:
            normalized["linked_invoice_id"] = None

        normalized["sender_account_age_days"] = normalized[
            "sender_account_age_days"
        ].fillna(0).astype(int)

        normalized["receiver_account_age_days"] = normalized[
            "receiver_account_age_days"
        ].fillna(0).astype(int)

        normalized["amount"] = normalized["amount"].astype(float)
        normalized["transaction_type"] = normalized["transaction_type"].astype(str)
        normalized["timestamp"] = normalized["timestamp"].astype(str)
        normalized["description"] = normalized["description"].astype(str)
        normalized["location"] = normalized["location"].astype(str)

        return normalized

    @staticmethod
    def load_transactions(csv_path: Path) -> list[Transaction]:
        """
        Parse transactions.csv
        """

        try:

            df = pd.read_csv(csv_path)

        except Exception:

            raise HTTPException(
                status_code=400,
                detail="Unable to read transactions CSV."
    

        df = CSVService.normalize_transactions(df)

        CSVService.validate_columns(
            df,
            CSVService.REQUIRED_TRANSACTION_COLUMNS,
        )

        transactions = []

        for row in df.to_dict(orient="records"):

            transactions.append(
                Transaction(**row)
            )

        return transactions

    @staticmethod
    def normalize_invoices(df: pd.DataFrame) -> pd.DataFrame:
        """
        Map the shipped invoice CSV schema to the backend model fields.
        """

        normalized = df.copy()

        if "gst_number" not in normalized.columns:
            normalized["gst_number"] = normalized.get(
                "vendor_gstin",
                "",
            )

        normalized["amount"] = normalized["amount"].astype(float)
        normalized["invoice_date"] = normalized["invoice_date"].astype(str)
        normalized["payment_status"] = normalized["payment_status"].astype(str)
        normalized["gst_number"] = normalized["gst_number"].astype(str)
        normalized["vendor_name"] = normalized["vendor_name"].astype(str)

        return normalized

    @staticmethod
    def load_invoices(csv_path: Path) -> list[Invoice]:
        """
        Parse invoices.csv
        """

        try:

            df = pd.read_csv(csv_path)

        except Exception:

            raise HTTPException(
                status_code=400,
                detail="Unable to read invoices CSV."
            )

        df = CSVService.normalize_invoices(df)

        CSVService.validate_columns(
            df,
            CSVService.REQUIRED_INVOICE_COLUMNS,
        )

        invoices = []

        for row in df.to_dict(orient="records"):

            invoices.append(
                Invoice(**row)
            )

        return invoices