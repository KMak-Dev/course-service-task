from httpx import AsyncClient

from tests.conftest import create_provider


async def test_provider_cannot_access_other_providers_course(client: AsyncClient) -> None:
    provider_a = await create_provider(client, "Provider A")
    provider_b = await create_provider(client, "Provider B")

    create_response = await client.post(
        f"/providers/{provider_a}/courses",
        json={"title": "Secret course"},
    )
    assert create_response.status_code == 201
    course_id = create_response.json()["id"]

    get_response = await client.get(f"/providers/{provider_b}/courses/{course_id}")
    assert get_response.status_code == 404
