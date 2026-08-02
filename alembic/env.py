from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from app.modules.auth.models import Role, Authorization
from app.modules.file.models import File
from app.modules.users.models import User
from app.modules.professional_applications.models import ProfessionalApplication
from app.modules.professionals.models import ProfessionalProfile, professional_skills
from app.modules.skills.models import Skill
from app.modules.booking.models import Booking
from alembic import context

# Import your custom type at the top of env.py
from app.core.pydantic_middleware.custom_typedecorator import PydanticType

def render_custom_types(type_, obj, autogen_context):
    """
    Tells Alembic how to render custom TypeDecorators in migration files.
    """
    if type_ == "type" and isinstance(obj, PydanticType):
        # 1. Tell Alembic to add the JSONB import to the migration file
        autogen_context.imports.add("from sqlalchemy.dialects.postgresql import JSONB")
        # 2. Return the exact string you want in the migration file
        return "JSONB()"
    
    # Return False to let Alembic handle other types normally
    return False
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
        render_item=render_custom_types
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