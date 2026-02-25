import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings
from app.models import Base

# Database engine with connection pooling and health checks
# pool_pre_ping ensures stale connections are recycled
# Default isolation level: READ COMMITTED (PostgreSQL default)
# This provides optimal balance between consistency and performance
# MVCC handles concurrent transactions without explicit locking
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    echo=settings.log_sql_queries,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger = logging.getLogger("payment-api")
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.exception("Error initializing database: %s", e)
        raise



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Readiness probe helper to verify DB connectivity."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
     logger.error("Database connection check failed: %s", e)          
    return False
