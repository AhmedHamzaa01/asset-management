from fastapi.testclient import TestClient


def test_bulk_import_inserts(client: TestClient, auth_headers):
    payload = {
        "assets": [
            {"type": "domain", "value": "example.com", "source": "scan"},
            {"type": "ip_address", "value": "1.2.3.4", "source": "scan"},
        ]
    }
    response = client.post("/api/v1/assets/import", json=payload, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 2
    assert body["updated"] == 0
    assert body["failed"] == 0


def test_duplicate_import_updates_not_inserts(client: TestClient, auth_headers):
    payload = {"assets": [{"type": "domain", "value": "example.com", "source": "scan"}]}

    client.post("/api/v1/assets/import", json=payload, headers=auth_headers)
    response = client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["inserted"] == 0
    assert body["updated"] == 1


def test_import_merges_tags(client: TestClient, auth_headers):
    client.post(
        "/api/v1/assets/import",
        json={"assets": [{"type": "domain", "value": "merge.com", "source": "scan", "tags": ["prod"]}]},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/assets/import",
        json={"assets": [{"type": "domain", "value": "merge.com", "source": "scan", "tags": ["critical"]}]},
        headers=auth_headers,
    )

    result = client.get("/api/v1/assets/?search=merge.com", headers=auth_headers).json()
    assets = result["items"]
    assert len(assets) == 1
    assert set(assets[0]["tags"]) == {"prod", "critical"}


def test_import_is_idempotent(client: TestClient, auth_headers):
    payload = {"assets": [{"type": "domain", "value": "idempotent.com", "source": "scan"}]}

    for _ in range(3):
        client.post("/api/v1/assets/import", json=payload, headers=auth_headers)

    result = client.get("/api/v1/assets/?search=idempotent.com", headers=auth_headers).json()
    assert len(result["items"]) == 1


def test_import_handles_malformed_record_gracefully(client: TestClient, auth_headers):
    """
    A batch with one valid and one invalid record must:
    - return 207 Multi-Status (partial success)
    - insert the good record
    - report the bad record as failed without crashing the batch
    """
    payload = {
        "assets": [
            {"type": "domain", "value": "good.com", "source": "scan"},
            {"type": "INVALID_TYPE", "value": "bad.com", "source": "scan"},
        ]
    }
    response = client.post("/api/v1/assets/import", json=payload, headers=auth_headers)
    assert response.status_code == 207
    body = response.json()
    assert body["inserted"] == 1
    assert body["failed"] == 1
    assert len(body["errors"]) == 1


def test_import_unauthenticated_rejected(client: TestClient):
    payload = {"assets": [{"type": "domain", "value": "x.com", "source": "scan"}]}
    response = client.post("/api/v1/assets/import", json=payload)
    assert response.status_code == 401