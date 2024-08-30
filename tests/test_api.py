import pytest
from materia.core import Config
from httpx import AsyncClient, Cookies
from io import BytesIO

# TODO: replace downloadable images for tests


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

    assert api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower()
    ).exists()

    info = await auth_client.get("/api/repository")
    assert info.status_code == 200, info.text

    delete = await auth_client.delete("/api/repository")
    assert delete.status_code == 200, delete.text

    info = await auth_client.get("/api/repository")
    assert info.status_code == 404, info.text

    # TODO: content


@pytest.mark.asyncio
async def test_directory(auth_client: AsyncClient, api_config: Config):
    first_dir_path = api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower(), "first_dir"
    )
    second_dir_path = api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower(), "second_dir"
    )
    second_dir_path_two = api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower(), "second_dir.1"
    )
    third_dir_path_one = api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower(), "third_dir"
    )
    third_dir_path_two = api_config.application.working_directory.joinpath(
        "repository", "PyTest".lower(), "second_dir", "third_dir"
    )

    create = await auth_client.post("/api/repository")
    assert create.status_code == 200, create.text

    create = await auth_client.post("/api/directory", json={"path": "first_dir"})
    assert create.status_code == 500, create.text

    create = await auth_client.post("/api/directory", json={"path": "/first_dir"})
    assert create.status_code == 200, create.text

    assert first_dir_path.exists()

    info = await auth_client.get("/api/directory", params=[("path", "/first_dir")])
    assert info.status_code == 200, info.text
    assert info.json()["used"] == 0
    assert info.json()["path"] == "/first_dir"

    create = await auth_client.patch(
        "/api/directory/rename",
        json={"path": "/first_dir", "name": "first_dir_renamed"},
    )
    assert create.status_code == 200, create.text

    delete = await auth_client.delete(
        "/api/directory", params=[("path", "/first_dir_renamed")]
    )
    assert delete.status_code == 200, delete.text

    assert not first_dir_path.exists()

    create = await auth_client.post("/api/directory", json={"path": "/second_dir"})
    assert create.status_code == 200, create.text

    create = await auth_client.post("/api/directory", json={"path": "/third_dir"})
    assert create.status_code == 200, create.text

    move = await auth_client.patch(
        "/api/directory/move", json={"path": "/third_dir", "target": "/second_dir"}
    )
    assert move.status_code == 200, move.text
    assert not third_dir_path_one.exists()
    assert third_dir_path_two.exists()

    info = await auth_client.get(
        "/api/directory", params=[("path", "/second_dir/third_dir")]
    )
    assert info.status_code == 200, info.text
    assert info.json()["path"] == "/second_dir/third_dir"

    copy = await auth_client.post(
        "/api/directory/copy",
        json={"path": "/second_dir", "target": "/", "force": True},
    )
    assert copy.status_code == 200, copy.text
    assert second_dir_path.exists()
    assert second_dir_path_two.exists()


@pytest.mark.asyncio
async def test_file(auth_client: AsyncClient, api_config: Config):
    create = await auth_client.post("/api/repository")
    assert create.status_code == 200, create.text

    async with AsyncClient() as client:
        pytest_logo_res = await client.get(
            "https://docs.pytest.org/en/stable/_static/pytest1.png"
        )
    assert isinstance(pytest_logo_res.content, bytes)
    pytest_logo = BytesIO(pytest_logo_res.content)

    create = await auth_client.post(
        "/api/file", files={"file": ("pytest.png", pytest_logo)}, data={"path": "/"}
    )
    assert create.status_code == 200, create.text
