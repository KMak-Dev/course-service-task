from httpx import AsyncClient

from tests.conftest import create_provider


async def _create_course(
    client: AsyncClient, provider_id: str, title: str = "Course"
) -> str:
    response = await client.post(
        f"/providers/{provider_id}/courses",
        json={"title": title},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_nested_chapters(client: AsyncClient) -> None:
    provider_id = await create_provider(client)
    course_id = await _create_course(client, provider_id)

    root_response = await client.post(
        f"/providers/{provider_id}/courses/{course_id}/chapters",
        json={"title": "Module 1"},
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]

    child_response = await client.post(
        f"/providers/{provider_id}/courses/{course_id}/chapters",
        json={"title": "Part A", "parent_id": root_id},
    )
    assert child_response.status_code == 201
    assert child_response.json()["parent_id"] == root_id

    list_response = await client.get(
        f"/providers/{provider_id}/courses/{course_id}/chapters",
        params={"parent_id": root_id},
    )
    assert list_response.status_code == 200
    chapters = list_response.json()
    assert len(chapters) == 1
    assert chapters[0]["id"] == child_response.json()["id"]


async def test_chapter_cannot_be_own_ancestor(client: AsyncClient) -> None:
    provider_id = await create_provider(client)
    course_id = await _create_course(client, provider_id)

    root_response = await client.post(
        f"/providers/{provider_id}/courses/{course_id}/chapters",
        json={"title": "Module 1"},
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]

    child_response = await client.post(
        f"/providers/{provider_id}/courses/{course_id}/chapters",
        json={"title": "Part A", "parent_id": root_id},
    )
    assert child_response.status_code == 201
    child_id = child_response.json()["id"]

    cycle_response = await client.patch(
        f"/providers/{provider_id}/courses/{course_id}/chapters/{root_id}",
        json={"parent_id": child_id},
    )
    assert cycle_response.status_code == 400
    assert (
        cycle_response.json()["detail"]
        == "Chapter cannot be its own ancestor"
    )
