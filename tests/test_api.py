from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database.connection import Base, get_db
from app.main import app
from app.models.address_model import UserAddress
from app.models.user_model import UserProfile

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_headers(auth_user_id: int) -> dict[str, str]:
    token = jwt.encode(
        {
            settings.JWT_USER_ID_CLAIM: (
                str(auth_user_id)
                if settings.JWT_USER_ID_CLAIM == "sub"
                else auth_user_id
            ),
            "exp": 4_102_444_800,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def profile_payload() -> dict[str, str]:
    return {"full_name": "Test Customer", "phone_number": "+14155550123"}


def address_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "address_type": "Home",
        "full_name": "Test Customer",
        "phone_number": "+14155550123",
        "address_line_1": "100 Main Street",
        "address_line_2": None,
        "city": "Example City",
        "state": "CA",
        "country": "US",
        "postal_code": "94105",
        "is_default": False,
    }
    payload.update(overrides)
    return payload


def test_profile_requires_valid_token(client: TestClient) -> None:
    assert client.get("/api/users/profile").status_code == 401
    assert (
        client.get(
            "/api/users/profile",
            headers={"Authorization": "Bearer invalid"},
        ).status_code
        == 401
    )
    fractional_user_id_token = jwt.encode(
        {
            settings.JWT_USER_ID_CLAIM: 1.5,
            "exp": 4_102_444_800,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.get(
            "/api/users/profile",
            headers={"Authorization": f"Bearer {fractional_user_id_token}"},
        ).status_code
        == 401
    )


def test_profiles_are_isolated_by_authenticated_user(client: TestClient) -> None:
    user_one = auth_headers(401)
    user_two = auth_headers(402)
    assert client.post(
        "/api/users/profile", headers=user_one, json=profile_payload()
    ).status_code == 201
    assert client.post(
        "/api/users/profile",
        headers=user_two,
        json={**profile_payload(), "full_name": "Second Customer"},
    ).status_code == 201

    assert (
        client.get("/api/users/profile", headers=user_one).json()["full_name"]
        == "Test Customer"
    )
    assert (
        client.get("/api/users/profile", headers=user_two).json()["full_name"]
        == "Second Customer"
    )


def test_profile_create_duplicate_read_update_and_delete(
    client: TestClient,
) -> None:
    headers = auth_headers(100)
    assert client.post(
        "/api/users/profile",
        headers=headers,
        json={**profile_payload(), "auth_user_id": 999},
    ).status_code == 422
    created = client.post(
        "/api/users/profile", headers=headers, json=profile_payload()
    )
    assert created.status_code == 201
    assert created.json()["auth_user_id"] == 100

    assert (
        client.post(
            "/api/users/profile", headers=headers, json=profile_payload()
        ).status_code
        == 409
    )
    assert client.get("/api/users/profile", headers=headers).status_code == 200
    assert (
        client.patch(
            "/api/users/profile",
            headers=headers,
            json={"full_name": "Updated Customer"},
        ).json()["full_name"]
        == "Updated Customer"
    )
    assert (
        client.get("/api/users/profile", headers=headers).json()["phone_number"]
        == profile_payload()["phone_number"]
    )
    assert (
        client.put(
            "/api/users/profile",
            headers=headers,
            json={
                **profile_payload(),
                "gender": "Other",
            },
        ).json()["gender"]
        == "Other"
    )
    assert client.delete("/api/users/profile", headers=headers).status_code == 204
    assert client.get("/api/users/profile", headers=headers).status_code == 404


def test_addresses_default_ownership_and_deactivation(client: TestClient) -> None:
    user_one = auth_headers(201)
    user_two = auth_headers(202)
    assert client.post(
        "/api/users/profile", headers=user_one, json=profile_payload()
    ).status_code == 201
    assert client.post(
        "/api/users/profile",
        headers=user_two,
        json={**profile_payload(), "full_name": "Other Customer"},
    ).status_code == 201

    first = client.post(
        "/api/users/addresses",
        headers=user_one,
        json=address_payload(is_default=True),
    )
    second = client.post(
        "/api/users/addresses",
        headers=user_one,
        json=address_payload(address_type="Office", is_default=True),
    )
    assert first.status_code == second.status_code == 201
    addresses = client.get("/api/users/addresses", headers=user_one).json()
    assert sum(address["is_default"] for address in addresses) == 1
    assert addresses[0]["is_default"] is False
    assert addresses[1]["is_default"] is True

    address_id = first.json()["id"]
    assert (
        client.get(f"/api/users/addresses/{address_id}", headers=user_one).status_code
        == 200
    )
    assert (
        client.get(f"/api/users/addresses/{address_id}", headers=user_two).status_code
        == 403
    )
    assert (
        client.get("/api/users/addresses/999999", headers=user_one).status_code
        == 404
    )
    updated = client.put(
        f"/api/users/addresses/{address_id}",
        headers=user_one,
        json=address_payload(city="Updated City"),
    )
    assert updated.status_code == 200
    assert updated.json()["city"] == "Updated City"
    assert (
        client.patch(
            f"/api/users/addresses/{address_id}/default",
            headers=user_one,
        ).status_code
        == 200
    )
    assert (
        client.get("/api/users/addresses", headers=user_one)
        .json()[0]["is_default"]
        is True
    )
    assert (
        client.delete(f"/api/users/addresses/{address_id}", headers=user_one).status_code
        == 204
    )
    assert (
        client.get(f"/api/users/addresses/{address_id}", headers=user_one).status_code
        == 404
    )
    assert client.post(
        "/api/users/profile/deactivate", headers=user_two
    ).status_code == 200
    assert client.get("/api/users/profile", headers=user_two).status_code == 403
    assert client.get("/api/users/addresses", headers=user_two).status_code == 403


def test_database_constraints_and_required_phone_validation(
    client: TestClient,
) -> None:
    headers = auth_headers(301)
    assert (
        client.post(
            "/api/users/profile",
            headers=headers,
            json={"full_name": "Test", "phone_number": "123"},
        ).status_code
        == 422
    )
    assert client.post(
        "/api/users/profile", headers=headers, json=profile_payload()
    ).status_code == 201

    db = TestingSessionLocal()
    try:
        assert db.query(UserProfile).count() == 1
        assert db.query(UserAddress).count() == 0
    finally:
        db.close()
