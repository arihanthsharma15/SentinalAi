from collections import defaultdict
from datetime import datetime

from models.transaction import Transaction


class TransactionRules:
    """
    Deterministic fraud detection rules for transactions.
    """

    # ---------- Configuration ----------

    STRUCTURING_THRESHOLD = 10000

    HIGH_VALUE_THRESHOLD = 25000

    NEW_ACCOUNT_DAYS = 30

    VELOCITY_WINDOW_MINUTES = 10

    VELOCITY_THRESHOLD = 5

    ODD_HOUR_START = 0
    ODD_HOUR_END = 5

    # -----------------------------------

    @staticmethod
    def evaluate(
        transactions: list[Transaction],
    ) -> dict[str, list[str]]:
        """
        Evaluate all transaction rules.

        Returns:
            {
                transaction_id: [
                    "Structuring",
                    "Odd Hours"
                ]
            }
        """

        flagged = defaultdict(list)

        sender_history = defaultdict(list)

        # Build sender transaction history
        for txn in transactions:
            sender_history[txn.sender_name].append(txn)

        # Evaluate every transaction
        for txn in transactions:

            rules = []

            if TransactionRules.is_structuring(txn):
                rules.append("Structuring")

            if TransactionRules.is_high_value_new_account(txn):
                rules.append("High Value + New Account")

            if TransactionRules.is_round_amount(txn):
                rules.append("Round Amount")

            if TransactionRules.is_odd_hour(txn):
                rules.append("Odd Hours")

            if TransactionRules.is_velocity(
                txn,
                sender_history[txn.sender_name]
            ):
                rules.append("Velocity")

            if rules:
                flagged[txn.transaction_id] = rules

        return flagged

    # ------------------------------------------------

    @staticmethod
    def is_structuring(txn: Transaction) -> bool:
        """
        Detect transactions just below reporting threshold.
        """

        return (
            TransactionRules.STRUCTURING_THRESHOLD - 100
            <= txn.amount <
            TransactionRules.STRUCTURING_THRESHOLD
        )

    @staticmethod
    def is_high_value_new_account(txn: Transaction) -> bool:
        """
        Large transfer from a recently created account.
        """

        return (
            txn.sender_account_age_days
            <= TransactionRules.NEW_ACCOUNT_DAYS
            and
            txn.amount
            >= TransactionRules.HIGH_VALUE_THRESHOLD
        )

    @staticmethod
    def is_round_amount(txn: Transaction) -> bool:
        """
        Suspicious round number.
        """

        return txn.amount % 1000 == 0

    @staticmethod
    def is_odd_hour(txn: Transaction) -> bool:
        """
        Late-night transaction.
        """

        hour = datetime.fromisoformat(
            txn.timestamp
        ).hour

        return (
            TransactionRules.ODD_HOUR_START
            <= hour
            <= TransactionRules.ODD_HOUR_END
        )

    @staticmethod
    def is_velocity(
        txn: Transaction,
        sender_transactions: list[Transaction],
    ) -> bool:
        """
        More than N transactions
        in a rolling time window.
        """

        current = datetime.fromisoformat(
            txn.timestamp
        )

        count = 0

        for other in sender_transactions:

            other_time = datetime.fromisoformat(
                other.timestamp
            )

            diff = abs(
                (current - other_time).total_seconds()
            ) / 60

            if diff <= TransactionRules.VELOCITY_WINDOW_MINUTES:
                count += 1

        return (
            count
            >= TransactionRules.VELOCITY_THRESHOLD
        )