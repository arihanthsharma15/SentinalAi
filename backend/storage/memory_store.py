from typing import List, Dict, Any


class MemoryStore:
    """
    Temporary in-memory storage for the current analysis session.

    In the future this class can be replaced by:
    - PostgreSQL
    - Redis
    - MongoDB

    without changing the routes or services.
    """

    def __init__(self):
        self._flagged_records: List[Dict[str, Any]] = []

    def save_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Replace existing records with new analysis results.
        """
        self._flagged_records = records

    def get_records(self) -> List[Dict[str, Any]]:
        """
        Return all flagged records.
        """
        return self._flagged_records

    def clear(self) -> None:
        """
        Clear all stored records.
        """
        self._flagged_records = []


# Singleton instance used across the application.
memory_store = MemoryStore()