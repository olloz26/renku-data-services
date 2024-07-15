"""Blueprints for the user endpoints."""

from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import rsa
from sanic import HTTPResponse, Request, json
from sanic.response import JSONResponse
from sanic_ext import validate

import renku_data_services.base_models as base_models
from renku_data_services.base_api.auth import authenticate, only_authenticated
from renku_data_services.base_api.blueprint import BlueprintFactoryResponse, CustomBlueprint
from renku_data_services.base_models.validation import validated_json
from renku_data_services.errors import errors
from renku_data_services.secrets.core import encrypt_user_secret
from renku_data_services.secrets.db import UserSecretsRepo
from renku_data_services.secrets.models import Secret, SecretKind
from renku_data_services.users import apispec
from renku_data_services.users.apispec_base import BaseAPISpec
from renku_data_services.users.db import UserRepo


class GetSecretsParams(BaseAPISpec):
    """The schema for the query parameters used when getting all secrets."""

    class Config:
        """Configuration."""

        extra = "ignore"

    kind: apispec.SecretKind = apispec.SecretKind.general


@dataclass(kw_only=True)
class KCUsersBP(CustomBlueprint):
    """Handlers for creating and listing users."""

    repo: UserRepo
    authenticator: base_models.Authenticator

    def get_all(self) -> BlueprintFactoryResponse:
        """Get all users or search by email."""

        @authenticate(self.authenticator)
        async def _get_all(request: Request, user: base_models.APIUser) -> JSONResponse:
            email_filter = request.args.get("exact_email")
            users = await self.repo.get_users(requested_by=user, email=email_filter)
            return validated_json(
                apispec.UsersWithId,
                [
                    dict(
                        id=user.user.id,
                        username=user.namespace.slug,
                        email=user.user.email,
                        first_name=user.user.first_name,
                        last_name=user.user.last_name,
                    )
                    for user in users
                ],
            )

        return "/users", ["GET"], _get_all

    def get_self(self) -> BlueprintFactoryResponse:
        """Get info about the logged in user."""

        @authenticate(self.authenticator)
        @only_authenticated
        async def _get_self(_: Request, user: base_models.APIUser) -> JSONResponse:
            if not user.is_authenticated or user.id is None:
                raise errors.Unauthorized(message="You do not have the required permissions for this operation.")
            user_info = await self.repo.get_or_create_user(requested_by=user, id=user.id)
            if not user_info:
                raise errors.MissingResourceError(message=f"The user with ID {user.id} cannot be found.")
            return validated_json(
                apispec.UserWithId,
                dict(
                    id=user_info.user.id,
                    username=user_info.namespace.slug,
                    email=user_info.user.email,
                    first_name=user_info.user.first_name,
                    last_name=user_info.user.last_name,
                ),
            )

        return "/user", ["GET"], _get_self

    def get_secret_key(self) -> BlueprintFactoryResponse:
        """Get the user's secret key.

        This is used to decrypt user secrets. This endpoint is only accessible from within the cluster.
        """

        @authenticate(self.authenticator)
        async def _get_secret_key(_: Request, user: base_models.APIUser) -> JSONResponse:
            secret_key = await self.repo.get_or_create_user_secret_key(requested_by=user)
            return json({"secret_key": secret_key})

        return "/user/secret_key", ["GET"], _get_secret_key

    def get_one(self) -> BlueprintFactoryResponse:
        """Get info about a specific user."""

        @authenticate(self.authenticator)
        async def _get_one(_: Request, user: base_models.APIUser, user_id: str) -> JSONResponse:
            user_info = await self.repo.get_or_create_user(requested_by=user, id=user_id)
            if not user_info:
                raise errors.MissingResourceError(message=f"The user with ID {user_id} cannot be found.")
            return validated_json(
                apispec.UserWithId,
                dict(
                    id=user_info.user.id,
                    username=user_info.namespace.slug,
                    email=user_info.user.email,
                    first_name=user_info.user.first_name,
                    last_name=user_info.user.last_name,
                ),
            )

        return "/users/<user_id>", ["GET"], _get_one


@dataclass(kw_only=True)
class UserSecretsBP(CustomBlueprint):
    """Handlers for user secrets.

    Secrets storage is jointly handled by data service and secret service.
    Each user has their own secret key 'user_secret', encrypted at rest, that only data service can decrypt.
    Secret service has a public private key combo where only it knows the private key. To store a secret,
    it is first encrypted with the user_secret, and then with a random password that is passed to the secret service by
    encrypting it with the secret service's public key and then storing both in the database. This way neither the data
    service nor the secret service can decrypt the secrets on their own.
    """

    secret_repo: UserSecretsRepo
    user_repo: UserRepo
    authenticator: base_models.Authenticator
    secret_service_public_key: rsa.RSAPublicKey

    def get_all(self) -> BlueprintFactoryResponse:
        """Get all user's secrets."""

        @authenticate(self.authenticator)
        @only_authenticated
        @validate(query=GetSecretsParams)
        async def _get_all(_: Request, user: base_models.APIUser, query: GetSecretsParams) -> JSONResponse:
            secret_kind = SecretKind[query.kind.value]
            secrets = await self.secret_repo.get_user_secrets(requested_by=user, kind=secret_kind)
            secrets_json = [
                secret.model_dump(include={"name", "id", "modification_date", "kind"}, exclude_none=True, mode="json")
                for secret in secrets
            ]
            return json(
                apispec.SecretsList(
                    root=[apispec.SecretWithId.model_validate(secret) for secret in secrets_json]
                ).model_dump(mode="json"),
                200,
            )

        return "/user/secrets", ["GET"], _get_all

    def get_one(self) -> BlueprintFactoryResponse:
        """Get a user secret."""

        @authenticate(self.authenticator)
        @only_authenticated
        async def _get_one(_: Request, user: base_models.APIUser, secret_id: str) -> JSONResponse:
            secret = await self.secret_repo.get_secret_by_id(requested_by=user, secret_id=secret_id)
            if not secret:
                raise errors.MissingResourceError(message=f"The secret with id {secret_id} cannot be found.")
            result = secret.model_dump(
                include={"name", "id", "modification_date", "kind"}, exclude_none=True, mode="json"
            )
            return json(result)

        return "/user/secrets/<secret_id>", ["GET"], _get_one

    def post(self) -> BlueprintFactoryResponse:
        """Create a new secret."""

        @authenticate(self.authenticator)
        @only_authenticated
        @validate(json=apispec.SecretPost)
        async def _post(_: Request, user: base_models.APIUser, body: apispec.SecretPost) -> JSONResponse:
            encrypted_value, encrypted_key = await encrypt_user_secret(
                user_repo=self.user_repo,
                requested_by=user,
                secret_service_public_key=self.secret_service_public_key,
                secret_value=body.value,
            )
            secret = Secret(
                name=body.name,
                encrypted_value=encrypted_value,
                encrypted_key=encrypted_key,
                kind=SecretKind[body.kind.value],
            )
            inserted_secret = await self.secret_repo.insert_secret(requested_by=user, secret=secret)
            result = inserted_secret.model_dump(
                include={"name", "id", "modification_date", "kind"}, exclude_none=True, mode="json"
            )
            return json(result, 201)

        return "/user/secrets", ["POST"], _post

    def patch(self) -> BlueprintFactoryResponse:
        """Update a specific secret."""

        @authenticate(self.authenticator)
        @only_authenticated
        @validate(json=apispec.SecretPatch)
        async def _patch(
            _: Request, user: base_models.APIUser, secret_id: str, body: apispec.SecretPatch
        ) -> JSONResponse:
            encrypted_value, encrypted_key = await encrypt_user_secret(
                user_repo=self.user_repo,
                requested_by=user,
                secret_service_public_key=self.secret_service_public_key,
                secret_value=body.value,
            )
            updated_secret = await self.secret_repo.update_secret(
                requested_by=user, secret_id=secret_id, encrypted_value=encrypted_value, encrypted_key=encrypted_key
            )
            result = updated_secret.model_dump(
                include={"name", "id", "modification_date", "kind"}, exclude_none=True, mode="json"
            )

            return json(result)

        return "/user/secrets/<secret_id>", ["PATCH"], _patch

    def delete(self) -> BlueprintFactoryResponse:
        """Delete a specific secret."""

        @authenticate(self.authenticator)
        @only_authenticated
        async def _delete(_: Request, user: base_models.APIUser, secret_id: str) -> HTTPResponse:
            await self.secret_repo.delete_secret(requested_by=user, secret_id=secret_id)
            return HTTPResponse(status=204)

        return "/user/secrets/<secret_id>", ["DELETE"], _delete
