"""Alembic setup and environment used for database migrations."""
from renku_data_services.migrations.env import run_migrations
from renku_data_services.resource_pool_adapters.schemas import BaseORM

target_metadata = BaseORM.metadata
run_migrations(target_metadata)