"""Custom Sanic Middleware."""

from sanic import Request

from renku_data_services import errors


async def validate_null_byte(request: Request) -> None:
    """Validate that a request does not contain a null byte."""
    if b"\\u0000" in request.body:
        raise errors.ValidationError(message="Null byte found in request")
