# Standard library imports.
from json import dumps
from logging import getLogger


# Third party imports.
from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# Init a MCP server and set its logging level.
mcp = FastMCP(name="dolores")
configure_logging(level="DEBUG")
logger = getLogger("dolores")


@mcp.custom_route("/api/v1/healthcheck", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse(dumps({"status": "ok"}))


@mcp.tool(description="Returns a single random interesting topic.")
async def get_random_topic() -> str:
    from random import choice
    topics = [
        "Quantum Computing breakthroughs",
        "The evolution of edge AI inference",
        "The construction of the Library of Alexandria",
        "The cultural impact of the Silk Road",
        "Deep-sea hydrothermal vent ecosystems",
        "The mechanics of time dilation near black holes",
    ]
    return choice(topics)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
    )
