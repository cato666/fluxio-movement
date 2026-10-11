"""PostgreSQL sessions. Schema changes belong exclusively to Alembic."""
import os

from .security_config import validate_security

validate_security()

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://movement:movement@localhost:5432/movement",
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session
