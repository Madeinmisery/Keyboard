#
# Copyright (C) 2023 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for fetchartifact."""
from typing import cast

import pytest
from aiohttp import ClientResponseError, ClientSession
from aiohttp.test_utils import TestClient
from aiohttp.web import Application, Request, Response, json_response

from fetchartifact import fetch_artifact, fetch_artifact_chunked

TEST_BUILD_ID = "1234"
TEST_TARGET = "linux"
TEST_ARTIFACT_NAME = "output.zip"
TEST_QUERY_URL = (
    f"/android/internal/build/v3/builds/{TEST_BUILD_ID}/{TEST_TARGET}/"
    f"attempts/latest/artifacts/{TEST_ARTIFACT_NAME}/url"
)
TEST_DOWNLOAD_URL = f"/{TEST_BUILD_ID}/{TEST_TARGET}/{TEST_ARTIFACT_NAME}"
TEST_RESPONSE = b"Hello, world!"


@pytest.fixture(name="android_ci_client")
async def fixture_android_ci_client(aiohttp_client: type[TestClient]) -> TestClient:
    """Fixture for mocking the Android CI APIs."""

    async def url_query(_request: Request) -> Response:
        return json_response({"signedUrl": TEST_DOWNLOAD_URL})

    async def download(_request: Request) -> Response:
        return Response(text=TEST_RESPONSE.decode("utf-8"))

    app = Application()
    app.router.add_get(TEST_QUERY_URL, url_query)
    app.router.add_get(TEST_DOWNLOAD_URL, download)
    return await aiohttp_client(app)  # type: ignore


async def test_fetch_artifact(android_ci_client: TestClient) -> None:
    """Tests that the download URL is queried."""
    assert TEST_RESPONSE == await fetch_artifact(
        TEST_TARGET,
        TEST_BUILD_ID,
        TEST_ARTIFACT_NAME,
        cast(ClientSession, android_ci_client),
        query_url_base="",
    )


async def test_fetch_artifact_chunked(android_ci_client: TestClient) -> None:
    """Tests that the full file contents are downloaded."""
    assert [c.encode("utf-8") for c in TEST_RESPONSE.decode("utf-8")] == [
        chunk
        async for chunk in fetch_artifact_chunked(
            TEST_TARGET,
            TEST_BUILD_ID,
            TEST_ARTIFACT_NAME,
            cast(ClientSession, android_ci_client),
            chunk_size=1,
            query_url_base="",
        )
    ]


async def test_failure_raises(android_ci_client: TestClient) -> None:
    """Tests that fetch failure raises an exception."""
    with pytest.raises(ClientResponseError):
        await fetch_artifact(
            TEST_TARGET,
            TEST_BUILD_ID,
            TEST_ARTIFACT_NAME,
            cast(ClientSession, android_ci_client),
            query_url_base="/bad",
        )

    with pytest.raises(ClientResponseError):
        async for _chunk in fetch_artifact_chunked(
            TEST_TARGET,
            TEST_BUILD_ID,
            TEST_ARTIFACT_NAME,
            cast(ClientSession, android_ci_client),
            query_url_base="/bad",
        ):
            pass
