#!/usr/bin/env python3
#
# Copyright (C) 2024 The Android Open Source Project
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

"""Faster implementation of `repo status`

This script runs on Python 3.6 or newer, matching the repo script. It should pass with `pylint` and
`mypy`.

Ctrl-C/SIGINT doesn't work well -- you may have to hit it a few times. I think this can be fixed by
replacing multiprocessing with a custom process-based executor that correctly uses signal
masking/handling with setpgid. The Ninja build tool seems to get this right, so it can be used as a
reference.
"""

import argparse
import functools
import os
from pathlib import Path
import multiprocessing
import multiprocessing.pool
import subprocess
import re
import sys
from typing import List, Optional, Sequence, Set, Union


# Virtual terminal (VT) escape sequences for changing text attributes.
VT_RESET = "\x1b[0m"
VT_BOLD = "\x1b[1m"
VT_GREEN = "\x1b[32m"
VT_RED = "\x1b[31m"
VT_CYAN = "\x1b[36m"

VT_ATTRIB_RE = re.compile(r"\x1b\[\d+m")
GIT_SHA_RE = re.compile(r"[0-9a-f]+$")


def strip_vt_attrib(text: str) -> str:
    """Remove text-attribute escape sequences from the string."""
    return VT_ATTRIB_RE.sub("", text)


def git_output(path: Path, args: Sequence[Union[str, Path]], strip=True, check=True) -> str:
    """Invoke `git` in a checkout, capturing its output."""
    output = subprocess.run(["git", "-C"] + [path] + list(args), encoding="utf8",
                            stdout=subprocess.PIPE, check=check).stdout
    if strip:
        output = output.strip()
    return output


def get_operations_in_progress(path: Path) -> List[str]:
    """Return a list of special git operations in-progress in a checkout, such as a rebase."""
    # pylint: disable=multiple-statements
    result = []
    if (path / ".git/CHERRY_PICK_HEAD").is_file(): result.append("cherry-pick")
    if (path / ".git/rebase-apply").is_dir() or \
       (path / ".git/rebase-merge").is_dir(): result.append("rebase")
    if (path / ".git/REVERT_HEAD").is_file(): result.append("revert")
    return result


def base_ref_name(manifest_branch: str) -> str:
    """The per-git-project git ref that points at the commit that repo last synced to."""
    return f"refs/remotes/m/{manifest_branch}"


def has_pristine_head(path: Path, manifest_branch: str) -> bool:
    """Return true if HEAD is detached and points at refs/remotes/m/{manifest_branch}."""

    # There can be thousands of projects, and it is rare for more than a handful to be modified. It
    # is important to identify the clean projects as cheaply as possible, so read the files in .git
    # directly. git commands are especially expensive on gLinux machines because even a trivial
    # query creates a new trace file (see b/337532121).
    with open(path / ".git/HEAD", encoding="utf8") as f:
        head_commit = f.read().strip()
    if not GIT_SHA_RE.match(head_commit):
        return False
    manifest_branch_path = path / ".git" / base_ref_name(manifest_branch)
    if manifest_branch_path.is_file():
        with open(manifest_branch_path, encoding="utf8") as f:
            base_commit = f.read().strip()
        if head_commit == base_commit:
            return True

    # Sometimes the .gits/refs/remotes/m/{manifest_branch} file contains the name of another remote
    # rather than a commit hash. It seems to be fairly rare, though, so just fall back on
    # `git rev-parse` in those cases.
    base_commit = git_output(path, ["rev-parse", base_ref_name(manifest_branch)])
    return head_commit == base_commit


class ProjectStatus:  # pylint: disable=too-few-public-methods
    """The result of scanning a git project's status."""
    header: List[str]  # A list of VT-escape-laden table cells, one per column.
    dirty_text: str    # Lines of text to print after the header. Typically empty ("").

    # TODO: Switch to @dataclass with Python 3.7 and remove this __init__ method and the pylint
    # annotation above.
    def __init__(self, header: List[str], dirty_text: str):
        self.header = header
        self.dirty_text = dirty_text


def scan_project_status(manifest_branch: str, quiet: bool,
                        project: Path) -> Optional[ProjectStatus]:
    """Scan a single git checkout for its status. Return None if it hasn't been changed and matches
    what's specified in the repo manifest."""

    # Rely on `git status` to diff the working tree and the index against the HEAD commit.
    ops = get_operations_in_progress(project)
    git_status = git_output(project, ["status", "--short"])
    if has_pristine_head(project, manifest_branch) and not ops and not git_status:
        return None

    if quiet:
        return ProjectStatus(header=[str(project)], dirty_text="")

    # Branch name (or "no branch")
    branch = git_output(project, ["symbolic-ref", "-q", "--short", "HEAD"], check=False)
    if branch:
        branch = f"{VT_CYAN}{VT_BOLD}branch {branch}{VT_RESET}"
    else:
        branch = f"{VT_RED}no branch{VT_RESET}"

    # Show how many commits the HEAD commit is ahead of, and behind, the base commit.
    behind, ahead = git_output(project, ["rev-list", "--left-right", "--count",
                                         f"{base_ref_name(manifest_branch)}...HEAD"]).split("\t")
    if behind != "0" or ahead != "0":
        position = ""
        if ahead != "0":
            position += f"{VT_GREEN}↑{ahead}{VT_RESET}"
        if behind != "0":
            position += " " * (position != "")
            position += f"{VT_RED}↓{behind}{VT_RESET}"
        branch += f" [{position}]"

    # Include the current HEAD commit's title.
    title = git_output(project, ["show", "-s", "--format=%s", "HEAD"])
    if len(title) > 50:
        title = title[:50] + "..."

    dirty_text = "".join([f"{VT_RED}{op} in progress{VT_RESET}\n" for op in ops])
    if git_status:
        dirty_text += f"{VT_RED}{git_status}{VT_RESET}\n"

    return ProjectStatus(
        header=[f"{VT_BOLD}project {project}{VT_RESET}", branch, title],
        dirty_text=dirty_text,
    )


def get_manifest_branch() -> str:
    """Get the name of the manifest repository's branch"""
    setting = "branch.default.merge"
    branch = git_output(Path(".repo/manifests.git"), ["--bare", "config", setting])
    if not branch.startswith("refs/heads/"):
        sys.exit(f"error: {setting} ({branch}) does not start with refs/heads/")
    return branch.split("/", 2)[2]


def find_repo_root() -> Path:
    """Returns the canonical path to the parent directory of the CWD that contains a .repo
    subdirectory."""
    root = Path(os.getcwd()).resolve()
    while True:
        if (root / ".repo").exists():
            break
        if root == root.parent:
            sys.exit(f"error: cannot find enclosing repo checkout for {os.getcwd()}")
        root = root.parent
    if not (root / ".repo/project.list").exists():
        extra_error = ""
        if (root / ".pore").exists():
            extra_error = f" ({os.path.basename(__file__)} can't handle pore checkouts)"
        sys.exit(f"error: .repo/project.list missing in repo checkout {root}{extra_error}")
    return root


def find_git_project_containing_path(requested: Path, all_projects: List[Path]) -> Path:
    """Find the git project that contains the specified path."""
    match: Optional[Path] = None
    for proj in all_projects:
        if requested.is_relative_to(proj) and (match is None or str(proj) > str(match)):
            match = proj
    if match is None:
        sys.exit(f"error: project {requested} not found")
    return match


def get_project_list(requested_projects: List[Path]) -> List[Path]:
    """Read repo's list of projects and filter it according to the project arguments on the command
    line."""
    with open(".repo/project.list", encoding="utf8") as f:
        all_projects = [Path(path) for path in f.read().splitlines()]
        assert all_projects
    matched_projects: Set[Path] = set()
    for req in requested_projects:
        matched_projects.add(find_git_project_containing_path(req, all_projects))
    if matched_projects:
        all_projects = [p for p in all_projects if p in matched_projects]
        assert all_projects
    return all_projects


def create_pool(*args, **kwargs) -> multiprocessing.pool.Pool:
    """Create a multiprocessing Pool with a reasonable choice of context.

    Python 3.12 and below still default to the "fork" context, which breaks threads. Use
    "forkserver" instead to be safer, and for more consistency when Python changes the default.
    https://discuss.python.org/t/switching-default-multiprocessing-context-to-spawn-on-posix-as-well/21868/17.
    """
    context = "forkserver" if sys.platform == "linux" else "spawn"
    return multiprocessing.get_context(context).Pool(*args, **kwargs)


def print_output(results: List[ProjectStatus]) -> None:
    """Print the final status table. Each entry has a few columns (or just one in quiet mode).
    Each entry may also have `git status` output after it listing changed files."""
    table_cell_lens = [[len(strip_vt_attrib(cell)) for cell in row.header]
                           for row in results]
    table_col_widths = [max(col) for col in zip(*table_cell_lens)]

    for entry in results:
        padding = 0
        for cell, width in zip(entry.header, table_col_widths):
            sys.stdout.write(padding * " ")
            sys.stdout.write(f"{cell}")
            padding = (width - len(strip_vt_attrib(cell))) + 4
        sys.stdout.write("\n")
        if entry.dirty_text != "":
            sys.stdout.write(entry.dirty_text)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="repo_quick_status",
        description="Report status across all git projects in the tree.")
    parser.add_argument("PROJECT", nargs="*", help="projects to scan for status", type=Path)
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress output")
    parser.add_argument("-j", "--jobs", default=os.cpu_count(), type=int,
                        help=f"number of projects to scan at a time, defaults to CPU_COUNT "
                             f"({os.cpu_count()})")
    args = parser.parse_args()

    repo_root = find_repo_root()

    # Adjust path arguments to be relative to the repo root.
    requested_projects = []
    for path in args.PROJECT:
        try:
            requested_projects.append(path.resolve().relative_to(repo_root))
        except ValueError:
            sys.exit(f"error: cannot canonicalize path {path} as a project in {repo_root}")

    # Change the CWD to the repo root for the rest of the script.
    os.chdir(repo_root)

    projects = get_project_list(requested_projects)
    manifest_branch = get_manifest_branch()

    with create_pool(processes=min(args.jobs, len(projects))) as pool:
        func = functools.partial(scan_project_status, manifest_branch, args.quiet)
        results: List[ProjectStatus] = \
            [r for r in pool.map(func, projects, chunksize=1) if r is not None]

    if results:
        print_output(results)
    elif not args.quiet:
        print("nothing to commit (working directory clean)")


if __name__ == "__main__":
    main()
