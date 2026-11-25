import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Fixture for calling a FastAPI app directly via an HTTP AsyncClient using ASGI transport."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await engine.dispose()


def test_password_hashing_and_jwt_roudtrip() -> None:
    """Unit test the hashing and encoding/decoding logic with Argon2id"""

    raw_pw = "DocMind@2026!"
    hashed = hash_password(raw_pw)
    assert hashed != raw_pw
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == user_id


async def test_auth_and_workspace_full_flow(async_client: AsyncClient) -> None:
    """Integration test full flow: Register -> Duplicate -> Login -> Get me -> Create & List Workspaces."""

    unique_suffix = uuid.uuid4().hex[:8]
    test_email = f"boss_{unique_suffix}@docmind.vn"
    test_slug = f"docmind-lab-{unique_suffix}"

    try:
        # 1. Register a new user (201 created)
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "StrongPassword123!",
                "full_name": "Boss DocMind",
            },
        )
        assert reg_res.status_code == 201
        user_data = reg_res.json()
        assert user_data["email"] == test_email
        assert "hashed_password" not in user_data

        # 2. Register an existed email -> 409 conflict
        dup_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "StrongPassword123!",
                "full_name": "Boss Duplicate",
            },
        )
        assert dup_res.status_code == 409
        assert dup_res.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

        # 3. Login wrong password -> 401 INVALID_CREDENTIALS
        bad_login = await async_client.post(
            "/api/v1/auth/login", json={"email": test_email, "password": "WrongPassword!"}
        )
        assert bad_login.status_code == 401
        assert bad_login.json()["error"]["code"] == "INVALID_CREDENTIALS"

        # 4. login successfully -> return JWT Bearer token
        login_res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": "StrongPassword123!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 5. Call API /api/v1/auth/me with Bearer token
        me_res = await async_client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == test_email

        # 6. Create a new workspace (201 Created)
        ws_res = await async_client.post(
            "/api/v1/workspaces",
            json={"name": "DocMind AI Lab", "slug": test_slug},
            headers=headers,
        )
        assert ws_res.status_code == 201
        assert ws_res.json()["slug"] == test_slug

        # 7. Create a new workspace with a duplicate slug -> 409 WORKSPACE_SLUG_EXISTS
        dup_ws_res = await async_client.post(
            "/api/v1/workspaces", json={"name": "Another Lab", "slug": test_slug}, headers=headers
        )
        assert dup_ws_res.status_code == 409
        assert dup_ws_res.json()["error"]["code"] == "WORKSPACE_SLUG_EXISTS"

        # 8. List workspaces of the current user
        list_ws_res = await async_client.get("/api/v1/workspaces", headers=headers)
        assert list_ws_res.status_code == 200
        workspaces = list_ws_res.json()
        assert any(w["slug"] == test_slug for w in workspaces)

    finally:
        # clean up the data test (CASCADE on workspace and workspace members)
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Workspace).where(Workspace.slug == test_slug))
            await session.execute(delete(User).where(User.email == test_email))
            await session.commit()
