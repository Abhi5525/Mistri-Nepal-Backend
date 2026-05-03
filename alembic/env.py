from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from app.modules.auth.models import Role, Authorization
from app.modules.file.models import File
from app.modules.users.models import User
from alembic import context

# Import your Base and settings
from app.core.db.database import Base
from app.core.config.config import settings

# Alembic Config object
config = context.config

# Set DB URL dynamically
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


# ---------------------------
# OFFLINE MODE
# ---------------------------
def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    
    url = settings.DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------
# ONLINE MODE (ASYNC)
# ---------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # important for schema changes
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ---------------------------
# ENTRY POINT
# ---------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()