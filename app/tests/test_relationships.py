from app.tests.conftest import (
    client,
    auth_headers,
)


def test_asset_graph():

    response = client.get(
        "/api/v1/assets/3/graph",
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert (
        "related_assets"
        in response.json()
    )