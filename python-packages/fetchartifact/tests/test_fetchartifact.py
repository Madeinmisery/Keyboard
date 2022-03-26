"""Tests for fetchartifact."""
import os
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import AsyncMock, Mock, patch

import pytest

from fetchartifact import fetch_artifact


@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_command_matches_inputs(
    mock_subproc: AsyncMock, mock_which: Mock
) -> None:
    """Tests that fetch_artifact is invoked with the expected arguments."""
    mock_which.return_value = "fetch_artifact"
    branch = "aosp-master-ndk"
    target = "linux"
    build = "1234"
    pattern = "android-ndk-*.zip"
    mock_subproc.return_value.returncode = 0
    await fetch_artifact(branch=branch, target=target, build=build, pattern=pattern)
    mock_subproc.assert_awaited_once_with(
        "fetch_artifact",
        "--use_oauth2",
        f"--branch={branch}",
        f"--target={target}",
        f"--bid={build}",
        pattern,
        cwd=Path(os.getcwd()),
    )


@patch.object(Path, "glob")
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_downloaded_artifacts_returned(
    mock_subproc: AsyncMock, mock_which: Mock, mock_glob: Mock
) -> None:
    """Tests that the paths to downloaded artifacts are returned."""
    mock_which.return_value = "fetch_artifact"
    mock_subproc.return_value.returncode = 0
    expected_artifacts = [Path("android-ndk-1234-linux-x86_64.zip")]
    mock_glob.return_value = expected_artifacts
    pattern = "android-ndk-*.zip"
    artifacts = await fetch_artifact(
        branch="aosp-master-ndk",
        target="linux",
        build="1234",
        pattern=pattern,
    )
    mock_glob.assert_called_once_with(pattern)
    assert artifacts == expected_artifacts


@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_failure_raises(mock_subproc: AsyncMock, mock_which: Mock) -> None:
    """Tests that fetch failure raises an exception."""
    mock_which.return_value = "fetch_artifact"
    mock_subproc.return_value.returncode = 1
    with pytest.raises(CalledProcessError):
        await fetch_artifact(
            branch="aosp-master-ndk",
            target="linux",
            build="1234",
            pattern="android-ndk-*.zip",
        )


@patch("shutil.which")
async def test_raises_if_fetch_artifact_not_installed(mock_which: Mock) -> None:
    """Tests that a missing fetch_artifact install raises an exception."""
    mock_which.return_value = None
    with pytest.raises(RuntimeError) as exc_info:
        await fetch_artifact(
            branch="aosp-master-ndk",
            target="linux",
            build="1234",
            pattern="android-ndk-*.zip",
        )

    assert "cannot find fetch_artifact" in str(exc_info.value)
