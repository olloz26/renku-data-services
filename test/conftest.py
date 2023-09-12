"""Fixtures for testing."""

import os

import pytest
from hypothesis import settings
from pytest_postgresql import factories

import renku_data_services.base_models as base_models
from renku_data_services.data_api.config import Config as DataConfig
from renku_data_services.migrations.core import run_migrations_for_app

settings.register_profile("ci", deadline=400)
settings.register_profile("dev", deadline=200)

settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


def init_db(**kwargs):
    """Run database migrations so they don't need to run on every test."""
    dummy_stores = os.environ.get("DUMMY_STORES")
    name = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    pw = os.environ.get("DB_PASSWORD")
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")

    os.environ["DUMMY_STORES"] = "true"
    os.environ["DB_NAME"] = kwargs["dbname"]
    os.environ["DB_USER"] = kwargs["user"]
    os.environ["DB_PASSWORD"] = kwargs["password"]
    os.environ["DB_HOST"] = kwargs["host"]
    os.environ["DB_PORT"] = str(kwargs["port"])

    config = DataConfig.from_env()
    run_migrations_for_app("storage", config.storage_repo)
    run_migrations_for_app("resource_pools", config.rp_repo)

    if dummy_stores:
        os.environ["DUMMY_STORES"] = dummy_stores
    else:
        del os.environ["DUMMY_STORES"]
    if name:
        os.environ["DB_NAME"] = name
    else:
        del os.environ["DB_NAME"]
    if user:
        os.environ["DB_USER"] = user
    else:
        del os.environ["DB_USER"]
    if pw:
        os.environ["DB_PASSWORD"] = pw
    else:
        del os.environ["DB_PASSWORD"]
    if host:
        os.environ["DB_HOST"] = host
    else:
        del os.environ["DB_HOST"]
    if port:
        os.environ["DB_PORT"] = port
    else:
        del os.environ["DB_PORT"]


postgresql_in_docker = factories.postgresql_noproc(load=[init_db])
postgresql = factories.postgresql("postgresql_in_docker")


@pytest.fixture
def user_repo(postgresql, monkeypatch):
    monkeypatch.setenv("DUMMY_STORES", "true")
    monkeypatch.setenv("DB_NAME", postgresql.info.dbname)
    config = DataConfig.from_env()
    yield config.user_repo
    monkeypatch.delenv("DUMMY_STORES", raising=False)


@pytest.fixture
def pool_repo(postgresql, monkeypatch):
    monkeypatch.setenv("DUMMY_STORES", "true")
    monkeypatch.setenv("DB_NAME", postgresql.info.dbname)
    config = DataConfig.from_env()
    yield config.rp_repo
    monkeypatch.delenv("DUMMY_STORES", raising=False)


@pytest.fixture
def storage_repo(postgresql, monkeypatch):
    monkeypatch.setenv("DUMMY_STORES", "true")
    monkeypatch.setenv("DB_NAME", postgresql.info.dbname)
    config = DataConfig.from_env()
    yield config.storage_repo
    monkeypatch.delenv("DUMMY_STORES", raising=False)


@pytest.fixture
def admin_user() -> base_models.APIUser:
    return base_models.APIUser(
        is_admin=True, id="some-random-id-123456", access_token="some-access-token"
    )  # nosec B106


@pytest.fixture
def loggedin_user() -> base_models.APIUser:
    return base_models.APIUser(
        is_admin=False, id="some-random-id-123456", access_token="some-access-token"
    )  # nosec B106


def only(iterable, default=None, too_long=None):
    """From https://github.com/python/importlib_resources/blob/v5.13.0/importlib_resources/_itertools.py#L2."""
    it = iter(iterable)
    first_value = next(it, default)

    try:
        second_value = next(it)
    except StopIteration:
        pass
    else:
        msg = "Expected exactly one item in iterable, but got {!r}, {!r}, " "and perhaps more.".format(
            first_value, second_value
        )
        raise too_long or ValueError(msg)

    return first_value