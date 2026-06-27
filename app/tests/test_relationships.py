import pytest
from fastapi.testclient import TestClient


def _create_asset(client, auth_headers, type_, value):
    r = client.post(
        "/api/v1/assets/",
        json={"type": type_, "value": value, "source": "scan"},
        headers=auth_headers,
    )
    return r.json()["id"]


def test_create_relationship(client: TestClient, auth_headers):
    domain_id = _create_asset(client, auth_headers, "domain", "example.com")
    sub_id = _create_asset(client, auth_headers, "subdomain", "api.example.com")

    response = client.post(
        "/api/v1/relationships",
        json={
            "source_asset_id": sub_id,
            "target_asset_id": domain_id,
            "relationship_type": "subdomain_of",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_asset_id"] == sub_id
    assert data["target_asset_id"] == domain_id


def test_duplicate_relationship_rejected(client: TestClient, auth_headers):
    domain_id = _create_asset(client, auth_headers, "domain", "example.com")
    sub_id = _create_asset(client, auth_headers, "subdomain", "api.example.com")

    payload = {
        "source_asset_id": sub_id,
        "target_asset_id": domain_id,
        "relationship_type": "subdomain_of",
    }
    client.post("/api/v1/relationships", json=payload, headers=auth_headers)
    response = client.post("/api/v1/relationships", json=payload, headers=auth_headers)
    assert response.status_code == 409


def test_get_asset_relationships(client: TestClient, auth_headers):
    domain_id = _create_asset(client, auth_headers, "domain", "example.com")
    sub_id = _create_asset(client, auth_headers, "subdomain", "api.example.com")

    client.post(
        "/api/v1/relationships",
        json={"source_asset_id": sub_id, "target_asset_id": domain_id, "relationship_type": "subdomain_of"},
        headers=auth_headers,
    )

    response = client.get(f"/api/v1/assets/{domain_id}/relationships", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_asset_graph(client: TestClient, auth_headers):
    domain_id = _create_asset(client, auth_headers, "domain", "example.com")
    sub_id = _create_asset(client, auth_headers, "subdomain", "api.example.com")

    client.post(
        "/api/v1/relationships",
        json={"source_asset_id": sub_id, "target_asset_id": domain_id, "relationship_type": "subdomain_of"},
        headers=auth_headers,
    )

    response = client.get(f"/api/v1/assets/{domain_id}/graph", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "asset" in body
    assert "related_assets" in body
    assert len(body["related_assets"]) == 1