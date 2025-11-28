"""SQLAlchemy base and database session configuration."""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def get_db():
    """Get database session dependency for FastAPI."""
    from core.database.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
