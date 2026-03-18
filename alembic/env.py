from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, pool
from alembic import context

# -----------------------------
# Load .env variables
# -----------------------------
load_dotenv()  # loads DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# -----------------------------
# Alembic Config object
# -----------------------------
config = context.config

# -----------------------------
# Logging configuration
# -----------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------
# Import your SQLAlchemy Base
# -----------------------------
from app.db.schema import Base  # your declarative Base
target_metadata = Base.metadata

# -----------------------------
# Offline migrations
# -----------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DBAPI needed)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# Online migrations
# -----------------------------
def run_migrations_online() -> None:
    """Run migrations in 'online' mode (DB connection required)."""
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},  # override config.ini dynamically
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# Run migrations in correct mode
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()