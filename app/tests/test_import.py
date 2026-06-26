
from app.tests.conftest import (
    client,
    auth_headers,
)


def test_duplicate_import_updates():

    payload = {
        "assets": [
            {
                "type": "domain",
                "value": "example.com"
            }
        ]
    }

    client.post(
        "/api/v1/assets/import",
        json=payload,
        headers=auth_headers,
    )

    response = client.post(
        "/api/v1/assets/import",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["updated"] == 1