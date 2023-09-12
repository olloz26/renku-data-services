# generated by datamodel-codegen:
#   filename:  api.spec.yaml
#   timestamp: 2023-09-08T13:54:00+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, RootModel

from renku_data_services.storage_schemas.base import BaseAPISpec


class Example(BaseAPISpec):
    value: Optional[str] = Field(None, description="a potential value for the option (think enum)")
    help: Optional[str] = Field(None, description="help text for the value")
    provider: Optional[str] = Field(
        None, description="The provider this value is applicable for. Empty if valid for all providers."
    )


class Datatype(Enum):
    int = "int"
    bool = "bool"
    string = "string"
    Time = "Time"


class RCloneOption(BaseAPISpec):
    name: Optional[str] = Field(None, description="name of the option")
    help: Optional[str] = Field(None, description="help text for the option")
    provider: Optional[str] = Field(
        None,
        description="The cloud provider the option is for (See 'provider' RCloneOption in the schema for potential values)",
        example="AWS",
    )
    default: Optional[Union[float, str, bool, Dict[str, Any]]] = Field(None, description="default value for the option")
    default_str: Optional[str] = Field(None, description="string representation of the default value")
    examples: Optional[List[Example]] = Field(
        None,
        description="These list potential values for this option, like an enum. With `excluse: true`, only a value from the list is allowed.",
    )
    required: Optional[bool] = Field(None, description="whether the option is required or not")
    ispassword: Optional[bool] = Field(None, description="whether the field is a password (use **** for display)")
    sensitive: Optional[bool] = Field(
        None,
        description="whether the value is sensitive (not stored in the service). Do not send this in requests to the service.",
    )
    advanced: Optional[bool] = Field(
        None, description="whether this is an advanced config option (probably don't show these to users)"
    )
    exclusive: Optional[bool] = Field(None, description="if true, only values from 'examples' can be used")
    datatype: Optional[Datatype] = Field(
        None, description="data type of option value. RClone has more options but they map to the ones listed here."
    )


class Error(BaseAPISpec):
    code: int = Field(..., example=1404, gt=0)
    detail: Optional[str] = Field(None, example="A more detailed optional message showing what the problem was")
    message: str = Field(..., example="Something went wrong - please try again later")


class ErrorResponse(BaseAPISpec):
    error: Error


class GitRequest(BaseAPISpec):
    project_id: str = Field(
        ...,
        description="Project id of a gitlab project (only int project id allowed, encoded as string for future-proofing)",
        example="123456",
        pattern="^[0-9]+$",
    )


class CloudStorageUrl(GitRequest):
    storage_url: str
    name: str = Field(..., description="Name of the storage", min_length=3, pattern="^[a-zA-Z0-9_-]+$")
    target_path: str = Field(
        ...,
        description="the target path relative to the repository where the storage should be mounted",
        example="my/project/folder",
    )
    private: bool = Field(False, description="Whether this storage is private (i.e. requires credentials) or not")


class CloudStorage(GitRequest):
    storage_type: Optional[str] = Field(
        None,
        description="same as rclone prefix/ rclone config type. Ignored in requests, but returned in responses for convenience.",
    )
    name: str = Field(..., description="Name of the storage", min_length=3, pattern="^[a-zA-Z0-9_-]+$")
    configuration: Dict[str, Optional[Union[float, str, bool, Dict[str, Any]]]] = Field(
        ...,
        description="Dictionary of rclone key:value pairs (based on schema from '/storage_schema'). Sensitive values are replaced with <sensitive> tokens",
    )
    source_path: str = Field(
        ...,
        description="the source path to mount, usually starts with bucket/container name",
        example="bucket/my/storage/folder/",
    )
    target_path: str = Field(
        ...,
        description="the target path relative to the repository where the storage should be mounted",
        example="my/project/folder",
    )
    private: bool = Field(False, description="Whether this storage is private (i.e. requires credentials) or not")


class CloudStoragePatch(BaseAPISpec):
    project_id: Optional[str] = Field(
        None,
        description="Project id of a gitlab project (only int project id allowed, encoded as string for future-proofing)",
        example="123456",
        pattern="^[0-9]+$",
    )
    storage_type: Optional[str] = Field(
        None,
        description="same as rclone prefix/ rclone config type. Ignored in requests, but returned in responses for convenience.",
    )
    configuration: Optional[Dict[str, Optional[Union[float, str, bool, Dict[str, Any]]]]] = Field(
        None, description="Dictionary of rclone key:value pairs (based on schema from '/storage_schema')"
    )
    source_path: Optional[str] = Field(
        None,
        description="the source path to mount, usually starts with bucket/container name",
        example="bucket/my/storage/folder/",
    )
    target_path: Optional[str] = Field(
        None,
        description="the target path relative to the repository where the storage should be mounted",
        example="my/project/folder",
    )
    private: Optional[bool] = Field(
        None, description="Whether this storage is private (i.e. requires credentials) or not"
    )


class CloudStorageWithId(CloudStorage):
    storage_id: str = Field(
        ..., description="ULID identifier of an object", max_length=26, min_length=26, pattern="^[A-Z0-9]+$"
    )


class CloudStorageGet(BaseAPISpec):
    storage: CloudStorageWithId
    sensitive_fields: Optional[List[RCloneOption]] = None


class RCloneEntry(BaseAPISpec):
    name: Optional[str] = Field(None, description="Human readable name of the provider")
    description: Optional[str] = Field(None, description="description of the provider")
    prefix: Optional[str] = Field(None, description="Machine readable name of the provider")
    options: Optional[List[RCloneOption]] = Field(None, description="Fields/properties used for this storage.")


class RCloneSchema(RootModel):
    root: List[RCloneEntry] = Field(..., description="List of RClone schemas for different storage types")