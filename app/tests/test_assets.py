from fastapi.testclient import TestClient


def _create(client, headers, type_="domain", value="example.com", source="manual"):
    r = client.post(
        "/api/v1/assets/",
        json={"type": type_, "value": value, "source": source},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def test_create_asset(client: TestClient, auth_headers):
    data = _create(client, auth_headers)
    assert data["value"] == "example.com"
    assert data["type"] == "domain"
    assert data["status"] == "active"


def test_get_asset(client: TestClient, auth_headers):
    asset_id = _create(client, auth_headers)["id"]
    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_update_asset(client: TestClient, auth_headers):
    asset_id = _create(client, auth_headers)["id"]
    response = client.put(
        f"/api/v1/assets/{asset_id}",
        json={"tags": ["prod", "critical"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "prod" in response.json()["tags"]


def test_update_asset_cannot_change_status(client: TestClient, auth_headers):
    """PUT must not accept a status field — lifecycle goes through dedicated endpoints."""
    asset_id = _create(client, auth_headers)["id"]
    response = client.put(
        f"/api/v1/assets/{asset_id}",
        json={"status": "archived"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_delete_asset_is_soft_archive(client: TestClient, auth_headers):
    asset_id = _create(client, auth_headers)["id"]
    client.delete(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.status_code == 404

def test_filter_assets_by_type(client: TestClient, auth_headers):
    _create(client, auth_headers, type_="domain", value="a.com")
    _create(client, auth_headers, type_="ip_address", value="1.2.3.4")

    response = client.get("/api/v1/assets/?type=domain", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert all(x["type"] == "domain" for x in body["items"])


def test_filter_assets_by_status(client: TestClient, auth_headers):
    _create(client, auth_headers, value="a.com")
    response = client.get("/api/v1/assets/?status=active", headers=auth_headers)
    assert response.status_code == 200
    assert all(x["status"] == "active" for x in response.json()["items"])


def test_pagination_returns_total(client: TestClient, auth_headers):
    for i in range(5):
        _create(client, auth_headers, value=f"domain{i}.com")

    response = client.get("/api/v1/assets/?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 5
    assert body["skip"] == 0
    assert body["limit"] == 2


def test_mark_asset_stale(client: TestClient, auth_headers):
    asset_id = _create(client, auth_headers, value="stale.com")["id"]
    response = client.patch(f"/api/v1/assets/{asset_id}/stale", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "stale"


def test_stale_asset_revives_on_reimport(client: TestClient, auth_headers):
    payload = {"assets": [{"type": "domain", "value": "revive.com", "source": "scan"}]}

    client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    asset_id = client.get("/api/v1/assets/?search=revive.com", headers=auth_headers).json()["items"][0]["id"]
    client.patch(f"/api/v1/assets/{asset_id}/stale", headers=auth_headers)

    client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    response = client.get(f"/api/v1/assets/{asset_id}", headers=auth_headers)
    assert response.json()["status"] == "active"


def test_unauthenticated_get_rejected(client: TestClient):
    assert client.get("/api/v1/assets/").status_code == 401


def test_unauthenticated_create_rejected(client: TestClient):
    r = client.post("/api/v1/assets/", json={"type": "domain", "value": "x.com", "source": "scan"})
    assert r.status_code == 401


def test_unauthenticated_delete_rejected(client: TestClient):
    assert client.delete("/api/v1/assets/1").status_code == 401
    
# 

def test_expired_certificate_status(client: TestClient, auth_headers):
    response = client.post(
    "/api/v1/assets/",
    json={
    "type": "certificate",
    "value": "CN=expired.example.com",
    "source": "scan",
    "extra_data": {
    "issuer": "Let's Encrypt",
    "expires": "2025-01-01T00:00:00+00:00",
    },
    },
    headers=auth_headers,
    )

    assert response.status_code == 201

    asset_id = response.json()["id"]

    response = client.get(
        f"/api/v1/assets/{asset_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "certificate"
    assert body["certificate_status"] == "expired"
    

def test_expiring_soon_certificate_status(client: TestClient, auth_headers):
    response = client.post(
    "/api/v1/assets/",
    json={
    "type": "certificate",
    "value": "CN=soon.example.com",
    "source": "scan",
    "extra_data": {
    "issuer": "Let's Encrypt",
    "expires": "2026-07-15T00:00:00+00:00",
    },
    },
    headers=auth_headers,
    )


    assert response.status_code == 201

    asset_id = response.json()["id"]

    response = client.get(
        f"/api/v1/assets/{asset_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "certificate"
    assert body["certificate_status"] == "expiring_soon"

def test_valid_certificate_status(client: TestClient, auth_headers):
    response = client.post(
    "/api/v1/assets/",
    json={
    "type": "certificate",
    "value": "CN=valid.example.com",
    "source": "scan",
    "extra_data": {
    "issuer": "Let's Encrypt",
    "expires": "2027-01-01T00:00:00+00:00",
    },
    },
    headers=auth_headers,
    )

    
    assert response.status_code == 201

    asset_id = response.json()["id"]

    response = client.get(
        f"/api/v1/assets/{asset_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["certificate_status"] == "valid"
    assert body["extra_data"]["certificate_status"] == "valid"

