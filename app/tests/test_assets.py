import pytest
from fastapi.testclient import TestClient


def test_create_asset(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/assets/",
        json={"type": "domain", "value": "example.com", "source": "manual"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "example.com"
    assert data["type"] == "domain"
    assert data["status"] == "active"


def test_get_asset(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/assets/",
        json={"type": "domain", "value": "example.com", "source": "manual"},
        headers=auth_headers,
    )
    asset_id = create.json()["id"]

    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_update_asset(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/assets/",
        json={"type": "domain", "value": "example.com", "source": "manual"},
        headers=auth_headers,
    )
    asset_id = create.json()["id"]

    response = client.put(
        f"/api/v1/assets/{asset_id}",
        json={"tags": ["prod", "critical"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "prod" in response.json()["tags"]


def test_delete_asset_is_soft_archive(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/assets/",
        json={"type": "domain", "value": "example.com", "source": "manual"},
        headers=auth_headers,
    )
    asset_id = create.json()["id"]

    client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)

    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.status_code == 404


def test_filter_assets_by_type(client: TestClient, auth_headers):
    client.post("/api/v1/assets/", json={"type": "domain", "value": "a.com", "source": "scan"}, headers=auth_headers)
    client.post("/api/v1/assets/", json={"type": "ip_address", "value": "1.2.3.4", "source": "scan"}, headers=auth_headers)

    response = client.get("/api/v1/assets/?type=domain", headers=auth_headers)
    assert response.status_code == 200
    assert all(x["type"] == "domain" for x in response.json())


def test_filter_assets_by_status(client: TestClient, auth_headers):
    client.post("/api/v1/assets/", json={"type": "domain", "value": "a.com", "source": "scan"}, headers=auth_headers)

    response = client.get("/api/v1/assets/?status=active", headers=auth_headers)
    assert response.status_code == 200
    assert all(x["status"] == "active" for x in response.json())


def test_pagination(client: TestClient, auth_headers):
    for i in range(5):
        client.post(
            "/api/v1/assets/",
            json={"type": "domain", "value": f"domain{i}.com", "source": "scan"},
            headers=auth_headers,
        )

    response = client.get("/api/v1/assets/?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_mark_asset_stale(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/assets/",
        json={"type": "domain", "value": "stale.com", "source": "scan"},
        headers=auth_headers,
    )
    asset_id = create.json()["id"]

    response = client.patch(f"/api/v1/assets/{asset_id}/stale", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "stale"


def test_stale_asset_revives_on_reimport(client: TestClient, auth_headers):
    payload = {"assets": [{"type": "domain", "value": "revive.com", "source": "scan"}]}

    client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    asset_id = client.get("/api/v1/assets/?search=revive.com", headers=auth_headers).json()[0]["id"]
    client.patch(f"/api/v1/assets/{asset_id}/stale", headers=auth_headers)

    client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.json()["status"] == "active"


def test_unauthenticated_request_rejected(client: TestClient):
    response = client.get("/api/v1/assets/")
    assert response.status_code == 401