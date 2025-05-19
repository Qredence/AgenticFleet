"""
Database-specific exceptions for Agentic Fleet.
"""


from agentic_fleet.exceptions.base import AgenticFleetDatabaseError


class DatabaseConnectionError(AgenticFleetDatabaseError):
    """
    Exception raised when a database connection fails.
    """

    def __init__(self, message: str = "Failed to connect to the database"):
        super().__init__(message)


class DatabaseQueryError(AgenticFleetDatabaseError):
    """
    Exception raised when a database query fails.
    """

    def __init__(self, message: str = "Database query failed", query: str | None = None):
        self.query = query
        super().__init__(message)


class DatabaseIntegrityError(AgenticFleetDatabaseError):
    """
    Exception raised when a database integrity constraint is violated.

    This includes unique constraint violations, foreign key violations, etc.
    """

    def __init__(self, message: str = "Database integrity constraint violated"):
        super().__init__(message)
