import pytest
from materia.config import Config
from httpx import AsyncClient, Cookies
from materia.models.base import Base
import aiofiles
from io import BytesIO


@pytest.mark.asyncio
async def test_auth(api_client: AsyncClient, api_config: Config):
    data = {"name": "PyTest", "password": "iampytest", "email": "pytest@example.com"}

    response = await api_client.post(
        "/api/auth/signup",
        json=data,
    )
    assert response.status_code == 200

    response = await api_client.post(
        "/api/auth/signin",
        json=data,
    )
    assert response.status_code == 200
    assert response.cookies.get(api_config.security.cookie_access_token_name)
    assert response.cookies.get(api_config.security.cookie_refresh_token_name)

    # TODO: conflict usernames and emails

    response = await api_client.get("/api/auth/signout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user(auth_client: AsyncClient, api_config: Config):
    info = await auth_client.get("/api/user")
    assert info.status_code == 200, info.text

    async with AsyncClient() as client:
        pytest_logo_res = await client.get(
            "https://docs.pytest.org/en/stable/_static/pytest1.png"
        )
    assert isinstance(pytest_logo_res.content, bytes)
    pytest_logo = BytesIO(pytest_logo_res.content)

    avatar = await auth_client.put(
        "/api/user/avatar",
        files={"file": ("pytest.png", pytest_logo)},
    )
    assert avatar.status_code == 200, avatar.text

    info = await auth_client.get("/api/user")
    avatar_info = info.json()["avatar"]
    assert avatar_info is not None
    assert api_config.application.working_directory.joinpath(
        "avatars", avatar_info
    ).exists()

    avatar = await auth_client.delete("/api/user/avatar")
    assert avatar.status_code == 200, avatar.text

    info = await auth_client.get("/api/user")
    assert info.json()["avatar"] is None
    assert not api_config.application.working_directory.joinpath(
        "avatars", avatar_info
    ).exists()

    delete = await auth_client.delete("/api/user")
    assert delete.status_code == 200, delete.text

    info = await auth_client.get("/api/user")
    assert info.status_code == 401, info.text


@pytest.mark.asyncio
async def test_repository(auth_client: AsyncClient, api_config: Config):
    info = await auth_client.get("/api/repository")
    assert info.status_code == 404, info.text

    create = await auth_client.post("/api/repository")
    assert create.status_code == 200, create.text

    create = await auth_client.post("/api/repository")
    assert create.status_code == 409, create.text

    info = await auth_client.get("/api/repository")
    assert info.status_code == 200, info.text
