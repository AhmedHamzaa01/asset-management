from app.tests.conftest import (
    client,
    auth_headers,
)


def test_filter_assets_by_type():

    response = client.get(
        "/api/v1/assets?type=domain",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        x["type"] == "domain"
        for x in data
    )