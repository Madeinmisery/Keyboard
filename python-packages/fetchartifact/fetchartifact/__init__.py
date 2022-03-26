"""A Python interface to http://go/fetchartifact."""
import asyncio
import logging
import os
import shutil
from logging import Logger
from pathlib import Path
from subprocess import CalledProcessError


def _logger() -> Logger:
    return logging.getLogger("fetchartifact")


def _make_fetch_command(
    branch: str, build: str, target: str, pattern: str
) -> list[str]:
    fetch_artifact_path = shutil.which("fetch_artifact")
    if fetch_artifact_path is None:
        raise RuntimeError(
            "error: cannot find fetch_artifact in PATH. Install it using:\n"
            "  sudo glinux-add-repo android\n"
            "  sudo apt update\n"
            "  sudo apt install android-fetch-artifact\n"
        )

    return [
        fetch_artifact_path,
        "--use_oauth2",
        f"--branch={branch}",
        f"--target={target}",
        f"--bid={build}",
        pattern,
    ]


async def fetch_artifact(
    *, branch: str, target: str, build: str, pattern: str
) -> list[Path]:
    """Fetches an artifact from the build server.

    Use OAuth2 authentication and the gLinux android-fetch-artifact package, which work
    with both on-corp and off-corp workstations.

    Artifacts are downloaded to the current working directory and are not automatically
    cleaned up.

    Returns:
        A list of paths to downloaded artifacts.
    """
    cwd = Path(os.getcwd())
    cmd = _make_fetch_command(branch, build, target, pattern)
    argv0 = cmd[0]
    args = cmd[1:]
    _logger().info("Fetching %s from build %s of %s/%s", pattern, build, branch, target)
    proc = await asyncio.create_subprocess_exec(argv0, *args, cwd=cwd)
    await proc.wait()
    assert proc.returncode is not None
    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, cmd, output=None, stderr=None)
    return list(cwd.glob(pattern))
