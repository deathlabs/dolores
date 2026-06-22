# Standard library imports.
import asyncio
from os import environ

# Third party imports.
from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain.messages import HumanMessage
from langchain_core.language_models.base import BaseLanguageModel
from langchain_mcp_adapters.client import MultiServerMCPClient


# Local imports.
from dolores.memory.checkpoint_saver import DjangoCheckpointSaver
from dolores.memory.store import DjangoStore
from dolores.models.openai import (
    get_openai_model,
    get_openai_model_from_azure,
)

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]
REPOSITORIES = environ.get("REPOSITORIES", "batman, superman, wonderwoman")


def build_model_client() -> BaseLanguageModel:
    """Builds a model client based on the model provider given."""
    match MODEL_PROVIDER:
        case "openai":
            return get_openai_model()
        case "azure_openai":
            return get_openai_model_from_azure()
        case _:
            raise ValueError("Invalid MODEL_PROVIDER. Options: openai or azure_openai.")


async def build_mcp_client():
    """Builds an MCP client for interacting with the Dolores MCP server."""
    client = MultiServerMCPClient(
        {
            "dolores": {
                "transport": "http",
                "url": TOOLS_ENDPOINT,
            }
        }
    )
    return await client.get_tools()


async def build_system_prompt(store: DjangoStore) -> str:
    """Builds the system prompt from procedural memory."""
    namespace = ("procedural", "dolores")
    rules = await store.asearch(namespace, limit=100)
    if not rules:
        return ""
    instructions = "\n".join(rule.value["instruction"] for rule in rules)
    return f"Instructions:\n{instructions}"


async def get_semantic_context(store: DjangoStore, repository: str) -> str:
    """Builds context for a given repository from semantic memory."""
    namespace = ("semantic", repository)
    memories = await store.asearch(namespace, limit=100)
    if not memories:
        return ""
    facts = "\n".join(memory.value["fact"] for memory in memories)
    return f"Known facts about this repository:\n{facts}"


def build_agent(
    model_client: BaseLanguageModel,
    mcp_client: MultiServerMCPClient,
    system_prompt: str,
    checkpointer: BaseCheckpointSaver,
    store: DjangoStore,
):
    """Builds a Dolores agent."""
    return create_agent(
        model=model_client,
        tools=mcp_client,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=store,
    )


async def run_agent_1(agent, store: DjangoStore, repository: str) -> None:
    """Tells a joke using randomly generated topics."""
    semantic_context = await get_semantic_context(store, repository)
    prompt = f"""
Current Repository: {repository}
{semantic_context}

Tell a joke using randomly generated topics. Don't repeat the same joke twice.
If you learn anything new or noteworthy about this repository, use your memory tool to save it.
    """
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"configurable": {"thread_id": f"agent1-{repository}"}},
    )
    print(result["messages"][-1].content)


async def main():
    """Starts Dolores."""
    model_client = build_model_client()
    mcp_client = await build_mcp_client()
    checkpointer = DjangoCheckpointSaver()
    store = DjangoStore()
    system_prompt = await build_system_prompt(store)
    repositories = [repo.strip() for repo in REPOSITORIES.split(",")]
    agent_1 = build_agent(model_client, mcp_client, system_prompt, checkpointer, store)

    for repository in repositories:
        await run_agent_1(agent_1, store, repository)


if __name__ == "__main__":
    asyncio.run(main())
