"""Database session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from ..core.config import get_config
from ..core.exceptions import DatabaseError
from .models import Base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    """Get database engine."""
    global _engine
    
    if _engine is None:
        config = get_config()
        db_config = config.database
        
        # Build connection string
        if db_config.url:
            connection_string = db_config.url
        else:
            connection_string = (
                f"postgresql://{db_config.user}:{db_config.password}@"
                f"{db_config.host}:{db_config.port}/{db_config.database}"
            )
        
        # Create engine with connection pooling
        # For SQLite, we might want to adjust pooling or args, but SQLAlchemy is generally robust.
        # However, check_same_thread is needed for SQLite if not using StaticPool, but standard queue pool is meant for multi-thread.
        engine_args = {
            "poolclass": QueuePool,
            "pool_size": db_config.pool_size,
            "max_overflow": db_config.max_overflow,
            "pool_pre_ping": True,  # Verify connections before using
            "echo": False,
        }
        
        if "sqlite" in connection_string:
             # SQLite specific adjustments if needed
             # Removing pool_size/max_overflow for SQLite default might be safer/cleaner but they are accepted by create_engine
             pass

        _engine = create_engine(connection_string, **engine_args)
        
        # Enable pgvector extension ONLY for Postgres
        if "postgresql" in connection_string:
            @event.listens_for(_engine, "connect", insert=True)
            def set_search_path(dbapi_conn, connection_record):
                with dbapi_conn.cursor() as cursor:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    dbapi_conn.commit()
        
        logger.info(f"Database engine created")
    
    return _engine


def get_session_local():
    """Get session factory."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session context manager."""
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise DatabaseError(f"Database operation failed: {e}") from e
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for DB session."""
    SessionLocal = get_session_local()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize database tables."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {e}") from e


def drop_db():
    """Drop all database tables."""
    try:
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise DatabaseError(f"Database drop failed: {e}") from e

