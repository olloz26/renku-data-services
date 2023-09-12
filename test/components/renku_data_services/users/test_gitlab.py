from unittest.mock import MagicMock
import pytest
import renku_data_services.users.gitlab as gitlab
import renku_data_services.errors as errors


def mock_gl_api(
    has_user: bool = True,
    user_state: str = "active",
    project_exists: bool = True,
    is_member: bool = True,
    access_level=30,
):
    gl_api = MagicMock()
    gl_api.return_value = gl_api
    if not has_user:
        gl_api.user.return_value = None
        return gl_api
    user = MagicMock()
    gl_api.user = user
    user.state = user_state
    user.id = "123456"
    project = MagicMock()
    if not project_exists:
        gl_api.projects.get.side_effect = gitlab.gitlab.GitlabGetError("Project not found")

    gl_api.projects.get.return_value = project

    if not is_member:
        project.members.get.side_effect = gitlab.gitlab.GitlabGetError("Member not found")
    member = MagicMock()
    project.members.get.return_value = member
    member.access_level = access_level
    return gl_api


def mock_request(json: bool = True):
    request = MagicMock()
    request.headers.get.return_value = "abcdefg"
    if json:
        request.json.__contains__.return_value = True
        request.json.__getitem__.return_value = {"project_id": "654321"}
    else:
        request.args.__contains__.return_value = True
        request.args.get.return_value = "654321"
    return request


@pytest.mark.asyncio
@pytest.mark.parametrize("json", [True, False])
async def test_gitlab_auth(json, monkeypatch):
    gl_mock = mock_gl_api()
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request(json)

        result = await gl_auth.authenticate("xxxxxx", request)
        assert result


@pytest.mark.asyncio
async def test_gitlab_auth_no_user(monkeypatch):
    gl_mock = mock_gl_api(has_user=False)
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request()

        with pytest.raises(errors.Unauthorized):
            await gl_auth.authenticate("xxxxxx", request)


@pytest.mark.asyncio
async def test_gitlab_auth_not_active(monkeypatch):
    gl_mock = mock_gl_api(user_state="inactive")
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request()

        with pytest.raises(errors.Unauthorized):
            await gl_auth.authenticate("xxxxxx", request)


@pytest.mark.asyncio
async def test_gitlab_auth_missing_project(monkeypatch):
    gl_mock = mock_gl_api(project_exists=False)
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request()

        with pytest.raises(errors.MissingResourceError):
            await gl_auth.authenticate("xxxxxx", request)


@pytest.mark.asyncio
async def test_gitlab_auth_not_member(monkeypatch):
    gl_mock = mock_gl_api(is_member=False)
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request()

        with pytest.raises(errors.Unauthorized):
            await gl_auth.authenticate("xxxxxx", request)


@pytest.mark.asyncio
async def test_gitlab_auth_not_admin(monkeypatch):
    gl_mock = mock_gl_api(access_level=10)
    with monkeypatch.context() as monkey:
        monkey.setattr(gitlab.gitlab, "Gitlab", gl_mock)
        gl_auth = gitlab.GitlabAuthenticator(gitlab_url="localhost")
        assert gl_auth.gitlab_url == "https://localhost"
        request = mock_request()

        result = await gl_auth.authenticate("xxxxxx", request)
        assert result
        assert not result.is_admin