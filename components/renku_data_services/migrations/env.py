"""Custom migrations env file to support modular migrations."""
import importlib
from logging.config import fileConfig
from typing import cast

from alembic import context
from alembic.config import Config
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateSchema

from renku_data_services.migrations.core import DataRepository


def include_object_factory(schema: str):
    """Filter only objects for the current database schema to be included."""

    def _include_object(object, name, type_, reflected, compare_to):
        if type_ == "table" and object.schema != schema:
            return False
        else:
            return True

    return _include_object


def run_migrations_offline(target_metadata, config: Config) -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    with cast(DataRepository, config.attributes.get("repo")).sync_engine.begin() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online(target_metadata, config: Config) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    with cast(DataRepository, config.attributes.get("repo")).sync_engine.begin() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_metadata.schema,
            include_schemas=True,
            include_object=include_object_factory(target_metadata.schema),
        )

        connection.execute(CreateSchema(target_metadata.schema, if_not_exists=True))

        with context.begin_transaction():
            context.run_migrations()


def run_migrations(metadata: MetaData):
    """Run migrations for a specific base model class."""
    # this is the Alembic Config object, which provides
    # access to the values within the .ini file in use.
    config = context.config

    if not config.attributes.get("repo"):
        config_class = config.get_section_option(config.config_ini_section, "config_class")

        if config_class is None:
            raise ValueError("Must set 'config_class' in alembic.ini section for app.")

        config_module = importlib.import_module(config_class)

        custom_config = config_module.Config.from_env()
        config.attributes["repo"] = custom_config.repo

    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    if context.is_offline_mode():
        run_migrations_offline(metadata, config)
    else:
        run_migrations_online(metadata, config)