"""
Database session management for Agentic Fleet.
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from agentic_fleet.database.base import Base

# Get database URL from environment variable or use SQLite as default
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./agentic_fleet.db")

# Create engine based on whether the URL is for an async database or not
if DATABASE_URL.startswith("postgresql+asyncpg"):
    # Async engine for PostgreSQL
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def get_db() -> Generator[AsyncSession, None, None]:
        """
        Get a database session.

        Yields:
            AsyncSession: Database session
        """
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

else:
    # Sync engine for SQLite or other databases
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
        echo=False,
        future=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db() -> Generator:
        """
        Get a database session.

        Yields:
            Session: Database session
        """
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


# Create all tables in the database
def create_tables() -> None:
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


def initialize_database() -> None:
    """
    Initialize the database.

    This function creates all tables and performs any other initialization tasks.
    """
    create_tables()
