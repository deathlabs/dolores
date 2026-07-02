# Third party imports.
from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_environment_tools(url: str):
    """Retrieves tools for interacting with the environment."""
    client = MultiServerMCPClient(
        {
            "dolores": {
                "transport": "http",
                "url": url,
            }
        }
    )
    return await client.get_tools()
