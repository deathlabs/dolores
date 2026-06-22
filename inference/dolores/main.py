# Standard library imports.
import asyncio
from os import environ

# Third party imports.
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models.base import BaseLanguageModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore

# Local imports.
from dolores.memory.short_term import DjangoCheckpointSaver
from dolores.memory.long_term import DjangoStore
from dolores.models.openai import (
    get_openai_model,
    get_openai_model_from_azure,
)

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]
REPOSITORIES = environ.get("REPOSITORIES", "deathlabs/emu, deathlabs/kaiju")


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


async def build_system_prompt(store: BaseStore) -> SystemMessage:
    """Builds the system prompt from procedural memory."""
    namespace = ("procedural", "dolores")
    rules = await store.asearch(namespace, limit=100)
    if not rules:
        return SystemMessage(content="")
    instructions = "\n".join(rule.value["instruction"] for rule in rules)
    return SystemMessage(content=f"Instructions:\n{instructions}")


async def get_semantic_context(store: BaseStore, repository: str) -> str:
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
    system_prompt: SystemMessage,
    checkpointer: BaseCheckpointSaver,
    store: BaseStore,
) -> CompiledStateGraph:
    """Builds a Dolores agent."""
    return create_agent(
        model=model_client,
        tools=mcp_client,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        store=store,
    )


async def observe_repository(
    agent: CompiledStateGraph, store: BaseStore, repository: str
) -> None:
    """Checks open PRs for a repository and records observations."""
    semantic_context = await get_semantic_context(store, repository)
    prompt = f"""
Current Repository: {repository}
{semantic_context}

Use the get_pull_requests tool to retrieve all pull requests for this repository.
For each pull request, use the get_pull_request_status tool to get its current status.

Look for what may be useful in the future, such as:
- Patterns in PR titles or branches that suggest the type of work being done
- PRs that have been open for an unusually long time
- Any signs of a change in language, framework, or tooling based on PR content
- Anything else noteworthy about the state of this repository

Summarize what you found.
    """
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"configurable": {"thread_id": f"observe-{repository}"}},
    )
    print(f"\n[{repository}]")
    print(result["messages"][-1].content)


async def main():
    """Starts Dolores."""
    model_client = build_model_client()
    mcp_client = await build_mcp_client()
    checkpointer = DjangoCheckpointSaver()
    store = DjangoStore()
    system_prompt = await build_system_prompt(store)
    repositories = [repo.strip() for repo in REPOSITORIES.split(",")]
    agent = build_agent(model_client, mcp_client, system_prompt, checkpointer, store)

    for repository in repositories:
        await observe_repository(agent, store, repository)


if __name__ == "__main__":
    asyncio.run(main())
