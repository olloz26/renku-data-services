"""Gitlab authenticator."""
import urllib.parse as parse
from dataclasses import dataclass

import gitlab
from sanic import Request

import renku_data_services.base_models as base_models
from renku_data_services import errors


@dataclass
class GitlabAuthenticator:
    """Authenticator for gitlab repos.

    Note:
        Once we have a project service, this should get information on what type of git provider is used from there
        and support different backends.
    """

    gitlab_url: str

    token_field: str = "Gitlab-Access-Token"

    def __post_init__(self):
        """Properly set gitlab url."""
        parsed_url = parse.urlparse(self.gitlab_url)

        if not parsed_url.scheme:
            self.gitlab_url = f"https://{self.gitlab_url}"

    async def authenticate(self, access_token: str, request: Request) -> base_models.APIUser:
        """Checks the validity of the access token."""
        if self.token_field != "Authorization":  # nosec: B105
            access_token = str(request.headers.get(self.token_field))

        project_id: str | None = None

        if request.json and "project_id" in request.json:
            project_id = request.json["project_id"]
        elif request.args and "project_id" in request.args:
            project_id = request.args.get("project_id")

        if project_id is not None:
            result = await self._auth_with_repo(access_token, project_id)
        else:
            raise errors.ValidationError(message="project_id not found")

        return result

    async def _auth_with_repo(self, access_token: str, project_id: str) -> base_models.APIUser:
        """Check if a user has access to a repository on gitlab."""
        client = gitlab.Gitlab(self.gitlab_url, oauth_token=access_token)
        try:
            client.auth()  # needed for the user property to be set
        except gitlab.GitlabAuthenticationError:
            raise errors.Unauthorized(message="User not authorized with Gitlab")
        user = client.user
        if user is None:
            raise errors.Unauthorized(message="User not authorized with Gitlab")

        if user.state != "active":
            raise errors.Unauthorized(message="User isn't active in Gitlab")

        user_id = user.id

        if user_id is None:
            raise errors.Unauthorized(message="Could not get user id")
        try:
            project = client.projects.get(id=project_id)
        except gitlab.GitlabGetError:
            raise errors.MissingResourceError(message=f"Couldn't find project {project_id} in Gitlab")
        try:
            member = project.members.get(id=user_id)
        except gitlab.GitlabGetError:
            raise errors.Unauthorized(message=f"User isn't a member of the project {project_id}")

        is_admin = False

        if member.access_level >= 30:
            # Developer, Maintainer and Owner
            is_admin = True

        return base_models.GitlabAPIUser(
            is_admin=is_admin, id=str(user_id), access_token=access_token, project_id=project_id
        )