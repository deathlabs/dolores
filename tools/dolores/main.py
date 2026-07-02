# Local imports.
from dolores.config import FASTMCP_PORT
from dolores.server import get_mcp_server


def main():
    """Start the Dolores MCP server."""
    mcp = get_mcp_server()
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=FASTMCP_PORT,
    )


if __name__ == "__main__":
    main()
