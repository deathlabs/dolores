# Standard library imports.
from json import dumps
from logging import getLogger

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


@mcp.custom_route("/api/v1/healthcheck", methods=["GET"])
async def health_check(request) -> PlainTextResponse:
    return PlainTextResponse(dumps({"status": "ok"}))


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
