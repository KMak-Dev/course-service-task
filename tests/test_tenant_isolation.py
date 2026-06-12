from httpx import AsyncClient

from tests.conftest import create_provider


async def test_provider_cannot_access_other_providers_course(
    client: AsyncClient,
) -> None:
    provider_a = await create_provider(client, "Provider A")
    provider_b = await create_provider(client, "Provider B")

    create_response = await client.post(
        f"/providers/{provider_a}/courses",
        json={"title": "Secret course"},
    )
    assert create_response.status_code == 201
    course_id = create_response.json()["id"]

    get_response = await client.get(
        f"/providers/{provider_b}/courses/{course_id}"
    )
    assert get_response.status_code == 404


async def test_provider_cannot_access_other_providers_lesson_video(
    client: AsyncClient,
) -> None:
    provider_a = await create_provider(client, "Provider A")
    provider_b = await create_provider(client, "Provider B")

    course_response = await client.post(
        f"/providers/{provider_a}/courses",
        json={"title": "Secret course"},
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    chapter_response = await client.post(
        f"/providers/{provider_a}/courses/{course_id}/chapters",
        json={"title": "Module 1"},
    )
    assert chapter_response.status_code == 201
    chapter_id = chapter_response.json()["id"]

    lesson_response = await client.post(
        f"/providers/{provider_a}/courses/{course_id}/chapters/{chapter_id}/lessons",
        json={"title": "Lesson 1"},
    )
    assert lesson_response.status_code == 201
    lesson_id = lesson_response.json()["id"]

    video_response = await client.post(
        f"/providers/{provider_a}/courses/{course_id}/chapters/{chapter_id}/lessons/{lesson_id}/video",
        json={
            "title": "Intro",
            "file_id": "file-secret",
            "subtitle_text": "Private subtitles",
        },
    )
    assert video_response.status_code == 201

    cross_tenant_response = await client.get(
        f"/providers/{provider_b}/courses/{course_id}/chapters/{chapter_id}/lessons/{lesson_id}/video",
    )
    assert cross_tenant_response.status_code == 404
