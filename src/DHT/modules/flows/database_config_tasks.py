#!/usr/bin/env python3
"""
DHT Database Configuration Tasks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Created database configuration generation tasks
# - Support for multiple database types
# - Migration tool configurations
# - Connection pooling and optimization settings
#

from prefect import task


@task(name="generate_alembic_config", description="Generate Alembic configuration")
def generate_alembic_config_task(
    database_url: str,
    script_location: str = "alembic",
    compare_type: bool = True,
    compare_server_default: bool = True,
) -> dict[str, str]:
    """Generate Alembic migration configuration.

    Args:
        database_url: Database connection URL
        script_location: Location of migration scripts
        compare_type: Compare column types
        compare_server_default: Compare server defaults

    Returns:
        Dict with alembic.ini and env.py content
    """
    configs = {}

    # alembic.ini
    configs["alembic.ini"] = f"""[alembic]
script_location = {script_location}
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = {database_url}

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

    # env.py
    configs["alembic/env.py"] = f"""from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import your models here
# from app.models import Base

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
# target_metadata = Base.metadata
target_metadata = None

def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.\"\"\"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
        compare_type={compare_type},
        compare_server_default={compare_server_default},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.\"\"\"
    # Allow database URL from environment
    database_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type={compare_type},
            compare_server_default={compare_server_default},
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

    return configs


@task(name="generate_sqlalchemy_config", description="Generate SQLAlchemy database config")
def generate_sqlalchemy_config_task(
    async_support: bool = True,
    use_pool: bool = True,
    pool_size: int = 5,
    max_overflow: int = 10,
    echo: bool = False,
) -> str:
    """Generate SQLAlchemy database configuration module.

    Args:
        async_support: Include async engine support
        use_pool: Use connection pooling
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
        echo: Echo SQL statements

    Returns:
        database.py content
    """
    if async_support:
        imports = """import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base"""
    else:
        imports = """import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker"""

    config = f"""{imports}

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

# Convert postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
"""

    if async_support:
        config += f"""
# Async engine configuration
engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo={echo},"""
    else:
        config += f"""
# Engine configuration
engine = create_engine(
    DATABASE_URL,
    echo={echo},"""

    if use_pool:
        config += f"""
    pool_size={pool_size},
    max_overflow={max_overflow},
    pool_pre_ping=True,
)"""
    else:
        config += """
    poolclass=NullPool,
)"""

    if async_support:
        config += """

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
"""
    else:
        config += """

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI/Flask
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
"""

    return config


@task(name="generate_redis_config", description="Generate Redis configuration")
def generate_redis_config_task(
    use_async: bool = True,
    connection_pool: bool = True,
    decode_responses: bool = True,
    serializer: str = "json",
) -> str:
    """Generate Redis client configuration.

    Args:
        use_async: Use async Redis client
        connection_pool: Use connection pooling
        decode_responses: Decode responses to strings
        serializer: Serialization method (json, pickle, msgpack)

    Returns:
        redis_client.py content
    """
    if use_async:
        imports = "import redis.asyncio as redis"
    else:
        imports = "import redis"

    if serializer == "json":
        imports += "\nimport json"
    elif serializer == "pickle":
        imports += "\nimport pickle"
    elif serializer == "msgpack":
        imports += "\nimport msgpack"

    config = f"""{imports}
import os
from typing import Any, Optional

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
"""

    if connection_pool:
        if use_async:
            config += f"""
# Connection pool
pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    decode_responses={decode_responses},
    max_connections=50,
)

# Redis client
redis_client = redis.Redis(connection_pool=pool)
"""
        else:
            config += f"""
# Connection pool
pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    decode_responses={decode_responses},
    max_connections=50,
)

# Redis client
redis_client = redis.Redis(connection_pool=pool)
"""
    else:
        config += f"""
# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses={decode_responses})
"""

    # Add serialization helpers
    if serializer == "json":
        config += """

def serialize(value: Any) -> str:
    \"\"\"Serialize value to JSON string.\"\"\"
    return json.dumps(value)

def deserialize(value: str) -> Any:
    \"\"\"Deserialize JSON string to value.\"\"\"
    return json.loads(value)
"""
    elif serializer == "pickle":
        config += """

def serialize(value: Any) -> bytes:
    \"\"\"Serialize value using pickle.\"\"\"
    return pickle.dumps(value)

def deserialize(value: bytes) -> Any:
    \"\"\"Deserialize pickle bytes to value.\"\"\"
    return pickle.loads(value)
"""
    elif serializer == "msgpack":
        config += """

def serialize(value: Any) -> bytes:
    \"\"\"Serialize value using msgpack.\"\"\"
    return msgpack.packb(value)

def deserialize(value: bytes) -> Any:
    \"\"\"Deserialize msgpack bytes to value.\"\"\"
    return msgpack.unpackb(value)
"""

    # Add cache decorator
    if use_async:
        config += """

def cache(key_prefix: str, ttl: int = 3600):
    \"\"\"Async cache decorator.\"\"\"
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}"

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return deserialize(cached)

            # Call function and cache result
            result = await func(*args, **kwargs)
            await redis_client.setex(
                cache_key,
                ttl,
                serialize(result)
            )
            return result
        return wrapper
    return decorator
"""
    else:
        config += """

def cache(key_prefix: str, ttl: int = 3600):
    \"\"\"Cache decorator.\"\"\"
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return deserialize(cached)

            # Call function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(
                cache_key,
                ttl,
                serialize(result)
            )
            return result
        return wrapper
    return decorator
"""

    return config


@task(name="generate_mongodb_config", description="Generate MongoDB configuration")
def generate_mongodb_config_task(
    database_name: str,
    use_async: bool = True,
    connection_pool_size: int = 100,
) -> str:
    """Generate MongoDB client configuration.

    Args:
        database_name: Name of the database
        use_async: Use async MongoDB client
        connection_pool_size: Connection pool size

    Returns:
        mongodb_client.py content
    """
    if use_async:
        imports = "from motor.motor_asyncio import AsyncIOMotorClient"
    else:
        imports = "from pymongo import MongoClient"

    config = f"""{imports}
import os
from typing import Optional

# MongoDB configuration
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "{database_name}")

# Client configuration
client_config = {{
    "maxPoolSize": {connection_pool_size},
    "minPoolSize": 10,
    "serverSelectionTimeoutMS": 5000,
}}
"""

    if use_async:
        config += """
# Async MongoDB client
client: Optional[AsyncIOMotorClient] = None
database = None

async def connect_to_mongo():
    \"\"\"Create database connection.\"\"\"
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL, **client_config)
    database = client[DATABASE_NAME]

async def close_mongo_connection():
    \"\"\"Close database connection.\"\"\"
    global client
    if client:
        client.close()

# FastAPI integration
def create_start_app_handler(app):
    async def start_app() -> None:
        await connect_to_mongo()
    return start_app

def create_stop_app_handler(app):
    async def stop_app() -> None:
        await close_mongo_connection()
    return stop_app
"""
    else:
        config += """
# MongoDB client
client = MongoClient(MONGODB_URL, **client_config)
database = client[DATABASE_NAME]

# Collections
users_collection = database["users"]
items_collection = database["items"]

# Indexes
def create_indexes():
    \"\"\"Create database indexes.\"\"\"
    users_collection.create_index([("email", 1)], unique=True)
    users_collection.create_index([("created_at", -1)])
    items_collection.create_index([("user_id", 1)])
    items_collection.create_index([("created_at", -1)])
"""

    return config


# Export all tasks
__all__ = [
    "generate_alembic_config_task",
    "generate_sqlalchemy_config_task",
    "generate_redis_config_task",
    "generate_mongodb_config_task",
]

