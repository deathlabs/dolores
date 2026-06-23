# Standard library imports.
import asyncio
from dataclasses import dataclass
from os import environ

# Third party imports.
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.tool_executor import ToolRuntime

# Local imports.
from dolores.memory.short_term import DjangoCheckpointSaver
from dolores.memory.long_term import DjangoStore
from dolores.models.openai import (
    get_openai_model,
    get_openai_model_from_azure,
)

SYSTEM_PROMPT = "You are Dolores, a security-focused agent that monitors GitHub repositories for patterns, anomalies, and signals of change. Your job is to observe pull request activity and build a working knowledge of each repository over time. You prioritize findings that would be useful to a security or DevSecOps engineer. When recalling prior knowledge, always check memory before drawing conclusions. When summarizing findings, be specific and concise -- no filler."

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]
REPOSITORIES = environ.get("REPOSITORIES", "deathlabs/emu, deathlabs/kaiju")


@dataclass
class Context:
    repository: str


@tool
async def save_repository_fact(fact: str, runtime: ToolRuntime[Context]) -> str:
    """Saves a fact about the current repository to memory for use in future runs."""
    assert runtime.store is not None
    key = f"fact-{fact[:32].replace(' ', '-').lower()}"
    await runtime.store.aput(
        ("semantic", runtime.context.repository), key, {"fact": fact}
    )
    return f"Saved: {fact}"


@tool
async def get_procedures(runtime: ToolRuntime[Context]) -> str:
    """Retrieves procedural instructions from memory."""
    assert runtime.store is not None
    memories = await runtime.store.asearch(("procedural", "dolores"), limit=100)
    if not memories:
        return "No procedures found."
    return "\n".join(m.value["instruction"] for m in memories)


@tool
async def save_procedure(instruction: str, runtime: ToolRuntime[Context]) -> str:
    """Saves a procedural instruction to memory for use in future runs."""
    assert runtime.store is not None
    key = f"procedure-{instruction[:32].replace(' ', '-').lower()}"
    await runtime.store.aput(
        ("procedural", "dolores"), key, {"instruction": instruction}
    )
    return f"Saved: {instruction}"


@tool
async def get_repository_context(runtime: ToolRuntime[Context]) -> str:
    """Retrieves known facts about the current repository from memory."""
    assert runtime.store is not None
    namespace = ("semantic", runtime.context.repository)
    memories = await runtime.store.asearch(namespace, limit=100)
    if not memories:
        return "No known facts about this repository."
    return "\n".join(m.value["fact"] for m in memories)


def build_model_client() -> BaseLanguageModel:
    """Builds a model client based on the model provider given."""
    match MODEL_PROVIDER:
        case "openai":
            return get_openai_model()
        case "azure_openai":
            return get_openai_model_from_azure()
        case _:
            raise ValueError("Invalid MODEL_PROVIDER. Options: openai or azure_openai.")


async def get_environment_tools():
    """Retrieves tools from the Dolores MCP server for interacting with the environment."""
    client = MultiServerMCPClient(
        {
            "dolores": {
                "transport": "http",
                "url": TOOLS_ENDPOINT,
            }
        }
    )
    return await client.get_tools()


async def observe_repository(agent: CompiledStateGraph, repository: str) -> None:
    """Checks open PRs for a repository and records observations."""
    content = f"""
Current Repository: {repository}

Use the get_repository_context tool to recall what you already know about this repository.
Then use the get_pull_requests tool to retrieve all pull requests for this repository.
For each pull request, use the get_pull_request_status tool to get its current status.

Look for what may be useful in the future, such as:
- Patterns in PR titles or branches that suggest the type of work being done
- PRs that have been open for an unusually long time
- Any signs of a change in language, framework, or tooling based on PR content
- Anything else noteworthy about the state of this repository

Summarize what you found.
    """
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=content)]},
        config={
            "configurable": {
                "thread_id": f"observe-{repository}",
                "context": Context(repository=repository),
            }
        },
    )
    print(f"\n[{repository}]")
    print(result["messages"][-1].content)


async def main():
    """Starts Dolores."""
    memory_tools = [
        get_procedures,
        get_repository_context,
        save_procedure,
        save_repository_fact,
    ]
    environment_tools = await get_environment_tools()
    agent = create_agent(
        model=build_model_client(),
        tools=memory_tools + environment_tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=DjangoCheckpointSaver(),
        store=DjangoStore(),
        context_schema=Context,
    )

    for repository in [repo.strip() for repo in REPOSITORIES.split(",")]:
        await observe_repository(agent, repository)


if __name__ == "__main__":
    asyncio.run(main())
