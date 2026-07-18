from schemas.response import FlaggedRecord, GemmaAnalysis

from rules.transaction_rules import TransactionRules
from rules.invoice_rules import InvoiceRules
from rules.cross_check import CrossCheckRules

from services.gemma_service import GemmaService


class AnalysisEngine:
    """
    Orchestrates the complete compliance analysis pipeline.
    """

    @staticmethod
    def process(transactions, invoices):
        """
        Complete pipeline.

        Transactions
            ↓
        Rules
            ↓
        Merge
            ↓
        AI Analysis
            ↓
        Frontend Response
        """

        transaction_flags = TransactionRules.evaluate(transactions)
        invoice_flags = InvoiceRules.evaluate(invoices)
        cross_flags = CrossCheckRules.evaluate(transactions, invoices)

        return AnalysisEngine.build_response(
            transactions,
            invoices,
            transaction_flags,
            invoice_flags,
            cross_flags,
        )

    @staticmethod
    def build_response(
        transactions,
        invoices,
        transaction_flags,
        invoice_flags,
        cross_flags,
    ):
        """
        Build frontend response.
        """

        records = []

        # ---------------------------------
        # Transaction Records
        # ---------------------------------

        for transaction in transactions:

            rules = []

            rules.extend(
                transaction_flags.get(
                    transaction.transaction_id,
                    []
                )
            )

            rules.extend(
                cross_flags.get(
                    transaction.transaction_id,
                    []
                )
            )

            if not rules:
                continue

            payload = {
                "record_type": "Transaction",
                "record": transaction.model_dump(),
                "triggered_rules": rules,
            }

            gemma = GemmaService.analyze(payload)

            records.append(
                FlaggedRecord(
                    id=transaction.transaction_id,
                    type="Transaction",
                    sender=transaction.sender_name,
                    receiver=transaction.receiver_name,
                    amount=transaction.amount,
                    rules_triggered=rules,
                    gemmaAnalysis=GemmaAnalysis(
                        risk_score=gemma["risk_score"],
                        risk_category=gemma["risk_category"],
                        explanation=gemma["explanation"],
                        recommended_action=gemma["recommended_action"],
                    ),
                )
            )

        # ---------------------------------
        # Invoice Records
        # ---------------------------------

        for invoice in invoices:

            rules = invoice_flags.get(
                invoice.invoice_id,
                []
            )

            if not rules:
                continue

            payload = {
                "record_type": "Invoice",
                "record": invoice.model_dump(),
                "triggered_rules": rules,
            }

            gemma = GemmaService.analyze(payload)

            records.append(
                FlaggedRecord(
                    id=invoice.invoice_id,
                    type="Invoice",
                    sender=invoice.vendor_name,
                    receiver="Accounts Payable",
                    amount=invoice.amount,
                    rules_triggered=rules,
                    gemmaAnalysis=GemmaAnalysis(
                        risk_score=gemma["risk_score"],
                        risk_category=gemma["risk_category"],
                        explanation=gemma["explanation"],
                        recommended_action=gemma["recommended_action"],
                    ),
                )
            )

        return records