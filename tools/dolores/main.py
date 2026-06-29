# Standard library imports.
from json import dumps
from logging import getLogger
from pathlib import Path
from subprocess import run

# Third party imports.
from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging
from starlette.responses import PlainTextResponse

# Local imports.
from dolores.clients.github import GitHubClient

# Init a MCP server and set its logging level.
mcp = FastMCP(name="dolores")
configure_logging(level="DEBUG")
logger = getLogger("dolores")

DOWNLOADS_DIR = Path("/home/dolores/downloads")


@mcp.custom_route("/api/v1/healthcheck", methods=["GET"])
async def health_check(request) -> PlainTextResponse:
    return PlainTextResponse(dumps({"status": "ok"}))


@mcp.tool(description="Clones a GitHub repository to a namespaced directory.")
async def git_clone(repo_name: str) -> str:
    client = GitHubClient(repo_name)
    url = client._repo.clone_url
    dest = DOWNLOADS_DIR / repo_name
    if dest.exists():
        return str(dest)
    dest.mkdir(parents=True, exist_ok=True)
    result = run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        dest.rmdir()
        return f"Clone failed: {result.stderr.strip()}"
    return str(dest)


@mcp.tool(description="Lists all files in a cloned repository.")
async def list_files(repo_name: str) -> str:
    repo_path = DOWNLOADS_DIR / repo_name
    if not repo_path.exists():
        return f"Repo not found: {repo_path}"
    paths = [
        str(p.relative_to(repo_path))
        for p in repo_path.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ]
    return dumps(sorted(paths))


@mcp.tool(description="Reads the contents of a file in a cloned repository.")
async def read_file(repo_name: str, file_path: str) -> str:
    repo_path = DOWNLOADS_DIR / repo_name
    target = (repo_path / file_path).resolve()
    if not target.is_relative_to(repo_path.resolve()):
        return "Access denied: path is outside the repository"
    if not target.exists():
        return f"File not found: {target}"
    try:
        return target.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool(description="Creates a new branch in a cloned repository.")
async def git_branch(repo_name: str, branch_name: str) -> str:
    repo_path = DOWNLOADS_DIR / repo_name
    if not repo_path.exists():
        return f"Repo not found: {repo_path}"
    result = run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )
    if result.returncode != 0:
        return f"Branch failed: {result.stderr.strip()}"
    return f"Created branch: {branch_name}"


@mcp.tool(description="Writes content to a file in a cloned repository.")
async def write_file(repo_name: str, file_path: str, content: str) -> str:
    repo_path = DOWNLOADS_DIR / repo_name
    target = (repo_path / file_path).resolve()
    if not target.is_relative_to(repo_path.resolve()):
        return "Access denied: path is outside the repository"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content)
        return f"Wrote: {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@mcp.tool(description="Commits and pushes changes in a cloned repository.")
async def git_push(repo_name: str, message: str) -> str:
    client = GitHubClient(repo_name)
    repo_path = DOWNLOADS_DIR / repo_name
    if not repo_path.exists():
        return f"Repo not found: {repo_path}"
    repo = client._repo
    branch = run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=repo_path,
    ).stdout.strip()
    changed = (
        run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        .stdout.strip()
        .splitlines()
    )
    for file_path in changed:
        target = repo_path / file_path
        content = target.read_text()
        try:
            existing = repo.get_contents(file_path, ref=branch)
            repo.update_file(file_path, message, content, existing.sha, branch=branch)
        except Exception:
            repo.create_file(file_path, message, content, branch=branch)
    return f"Pushed {len(changed)} file(s) to {branch}"


@mcp.tool(description="Fetches all pull requests for the given GitHub repository.")
async def get_pull_requests(repo_name: str) -> str:
    client = GitHubClient(repo_name)
    pull_requests = dumps(
        [
            {
                "number": pull_request.number,
                "title": pull_request.title,
                "url": pull_request.html_url,
                "branch": pull_request.head.ref,
                "created_at": pull_request.created_at.isoformat(),
            }
            for pull_request in client._repo.get_pulls(state="all")
        ]
    )
    return pull_requests


@mcp.tool(description="Fetches metadata for the given GitHub pull request.")
async def get_pull_request_status(repo_name: str, pull_request_number: int) -> str:
    client = GitHubClient(repo_name)
    pull_request = client._repo.get_pull(number=pull_request_number)
    metadata = dumps(
        {
            "number": pull_request.number,
            "title": pull_request.title,
            "url": pull_request.html_url,
            "state": pull_request.state,
            "merged": pull_request.merged,
            "mergeable": pull_request.mergeable,
            "branch": pull_request.head.ref,
            "created_at": pull_request.created_at.isoformat(),
            "updated_at": pull_request.updated_at.isoformat(),
            "closed_at": (
                pull_request.closed_at.isoformat() if pull_request.closed_at else None
            ),
            "merged_at": (
                pull_request.merged_at.isoformat() if pull_request.merged_at else None
            ),
        }
    )
    return metadata


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
    )
