from collections import defaultdict
from datetime import date, datetime

from models.invoice import Invoice


class InvoiceRules:
    """
    Deterministic fraud detection rules for invoices.
    """

    BLACKLISTED_VENDORS = {
        "Fake Corp",
        "Blacklisted Vendor",
        "Shell Company Ltd",
        "Unknown Holdings",
    }

    @staticmethod
    def evaluate(
        invoices: list[Invoice],
    ) -> dict[str, list[str]]:
        """
        Evaluate all invoice rules.

        Returns:
        {
            invoice_id: [
                "Duplicate Invoice",
                "Invalid GST"
            ]
        }
        """

        flagged = defaultdict(list)

        duplicate_counter = defaultdict(int)

        for invoice in invoices:
            key = (
                invoice.vendor_name.lower(),
                invoice.amount,
            )
            duplicate_counter[key] += 1

        for invoice in invoices:

            rules = []

            if InvoiceRules.is_duplicate(
                invoice,
                duplicate_counter,
            ):
                rules.append("Duplicate Invoice")

            if InvoiceRules.is_invalid_gst(invoice):
                rules.append("Invalid GST")

            if InvoiceRules.is_blacklisted_vendor(invoice):
                rules.append("Blacklisted Vendor")

            if InvoiceRules.is_future_date(invoice):
                rules.append("Future Date")

            if rules:
                flagged[invoice.invoice_id] = rules

        return flagged

    # --------------------------------------------------

    @staticmethod
    def is_duplicate(
        invoice: Invoice,
        duplicate_counter: dict,
    ) -> bool:

        key = (
            invoice.vendor_name.lower(),
            invoice.amount,
        )

        return duplicate_counter[key] > 1

    @staticmethod
    def is_invalid_gst(invoice: Invoice) -> bool:
        """
        Basic GST validation.

        Expected length = 15 characters.
        """

        gst = invoice.gst_number.strip()

        return len(gst) != 15

    @staticmethod
    def is_blacklisted_vendor(
        invoice: Invoice,
    ) -> bool:

        return (
            invoice.vendor_name
            in InvoiceRules.BLACKLISTED_VENDORS
        )

    @staticmethod
    def is_future_date(
        invoice: Invoice,
    ) -> bool:

        invoice_date = datetime.strptime(
            invoice.invoice_date,
            "%Y-%m-%d",
        ).date()

        return invoice_date > date.today()