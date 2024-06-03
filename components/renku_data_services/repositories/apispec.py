# generated by datamodel-codegen:
#   filename:  api.spec.yaml
#   timestamp: 2024-06-03T08:25:47+00:00

from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field
from renku_data_services.repositories.apispec_base import BaseAPISpec


class RepositoryPermissions(BaseAPISpec):
    model_config = ConfigDict(
        extra="forbid",
    )
    pull: bool
    push: bool


class Error(BaseAPISpec):
    code: int = Field(..., example=1404, gt=0)
    detail: Optional[str] = Field(
        None, example="A more detailed optional message showing what the problem was"
    )
    message: str = Field(..., example="Something went wrong - please try again later")


class ErrorResponse(BaseAPISpec):
    error: Error


class RepositoryMetadata(BaseAPISpec):
    model_config = ConfigDict(
        extra="forbid",
    )
    git_http_url: str = Field(
        ...,
        description="A URL which can be opened in a browser, i.e. a web page.",
        example="https://example.org",
    )
    web_url: str = Field(
        ...,
        description="A URL which can be opened in a browser, i.e. a web page.",
        example="https://example.org",
    )
    permissions: RepositoryPermissions


class RepositoryProviderMatch(BaseAPISpec):
    model_config = ConfigDict(
        extra="forbid",
    )
    provider_id: str = Field(
        ...,
        description='ID of a OAuth2 provider, e.g. "gitlab.com".',
        example="some-id",
    )
    connection_id: Optional[str] = Field(
        None,
        description="ULID identifier",
        max_length=26,
        min_length=26,
        pattern="^[A-Z0-9]{26}$",
    )
    repository_metadata: Optional[RepositoryMetadata] = None
