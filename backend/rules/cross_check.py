from collections import defaultdict

from models.transaction import Transaction
from models.invoice import Invoice


class CrossCheckRules:
    """
    Cross-check rules between transactions and invoices.
    """

    @staticmethod
    def evaluate(
        transactions: list[Transaction],
        invoices: list[Invoice],
    ) -> dict[str, list[str]]:
        """
        Cross-check linked invoices and transactions.

        Returns:
        {
            "TXN-1001": [
                "Amount Mismatch"
            ]
        }
        """

        flagged = defaultdict(list)

        invoice_lookup = {
            invoice.invoice_id: invoice
            for invoice in invoices
        }

        for transaction in transactions:

            if not transaction.linked_invoice_id:
                continue

            invoice = invoice_lookup.get(
                transaction.linked_invoice_id
            )

            if invoice is None:
                continue

            if (
                float(transaction.amount)
                !=
                float(invoice.amount)
            ):
                flagged[
                    transaction.transaction_id
                ].append("Amount Mismatch")

        return flagged