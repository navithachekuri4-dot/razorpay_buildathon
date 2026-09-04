from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
# In-memory SQLite (used by the test suite) needs a single shared
# connection across threads, or every new connection sees an empty DB.
engine_kwargs = {"connect_args": connect_args}
if settings.DATABASE_URL == "sqlite:///:memory:":
    engine_kwargs["poolclass"] = StaticPool
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: one DB session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
