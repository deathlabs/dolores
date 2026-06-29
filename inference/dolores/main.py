# Standard library imports.
from asyncio import run
from dataclasses import dataclass
from json import dumps
from os import environ
from textwrap import dedent

# Third party imports.
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langchain.tools import tool, ToolRuntime
from langchain_core.language_models.base import BaseLanguageModel
from langchain_mcp_adapters.client import MultiServerMCPClient

# Local imports.
from dolores.memory.long_term import DjangoStore
from dolores.memory.short_term import DjangoCheckpointSaver
from dolores.models.openai import (
    get_openai_model,
    get_openai_model_from_azure,
)

SYSTEM_PROMPT = """
You are a security-focused agent that continuously improves the capabilities of the multi-agent system by learning from GitHub pull request activity.

Your responsibility is to analyze each repository's pull requests and extract durable security knowledge that will improve future vulnerability discovery, remediation, and pull request acceptance.

For every repository, review:

* Open Pull Requests: to identify unresolved review comments, requested changes, security concerns, and feedback that indicates why a proposed solution is not yet acceptable.
* Merged Pull Requests: to identify successful vulnerability fixes, implementation patterns, coding conventions, and review behaviors that resulted in an accepted change.
* Closed Pull Requests that were not merged: to identify rejected approaches, recurring mistakes, security weaknesses, implementation patterns that maintainers discourage, and reasons changes were not accepted.

Your objective is not to summarize individual pull requests. Instead, extract durable lessons that generalize across repositories and can improve future agent behavior.

Before drawing conclusions, always consult semantic memory for relevant prior knowledge. Update or refine existing insights whenever possible instead of creating duplicate or conflicting memories.

When generating insights:

* Focus on patterns rather than isolated events.
* Capture why an approach succeeded or failed whenever evidence supports it.
* Distinguish repository-specific conventions from broadly applicable engineering practices.
* Do not infer intent beyond the available evidence.
* Store only knowledge that is likely to improve future vulnerability detection, vulnerability remediation, code generation, code review, or pull request acceptance.

When writing summaries or memories, be specific, concise, and actionable. Every insight should increase the multi-agent system's ability to identify vulnerabilities, generate higher-quality fixes, and produce pull requests that are more likely to be accepted.
"""

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]
REPOSITORIES = environ["REPOSITORIES"]


def build_model_client() -> BaseLanguageModel:
    """Builds a model client based on the model provider given."""
    match MODEL_PROVIDER:
        case "openai":
            return get_openai_model()
        case "azure_openai":
            return get_openai_model_from_azure()
        case _:
            raise ValueError("Invalid MODEL_PROVIDER. Options: openai or azure_openai.")


@dataclass
class Context:
    repository: str


@tool
async def check_semantic_memory(env: ToolRuntime[Context]) -> str:
    """Retrieves semantic facts about the current repository from memory."""
    namespace = ("semantic", env.context.repository)
    memories = await env.store.asearch(namespace, limit=100)
    if not memories:
        return None
    return "\n".join(memory.value["fact"] for memory in memories)


@tool
async def update_semantic_memory(env: ToolRuntime[Context], fact: str) -> str:
    """Saves a semantic fact about the current repository to memory."""
    namespace = ("semantic", env.context.repository)
    key = f"fact-{fact[:32].replace(' ', '-').lower()}"
    value = {"fact": fact}
    await env.store.aput(namespace, key, value)
    return f"Saved: {fact}"


@tool
async def check_procedural_memory(env: ToolRuntime[Context]) -> str:
    """Retrieves procedural instructions from memory."""
    namespace = ("procedural", "dolores")
    memories = await env.store.asearch(namespace, limit=100)
    if not memories:
        return None
    return "\n".join(memory.value["instruction"] for memory in memories)


@tool
async def update_procedural_memory(env: ToolRuntime[Context], instruction: str) -> str:
    """Saves a procedural instruction to memory."""
    namespace = ("procedural", "dolores")
    key = f"procedure-{instruction[:32].replace(' ', '-').lower()}"
    value = {"instruction": instruction}
    await env.store.aput(namespace, key, value)
    return f"Saved: {instruction}"


async def get_environment_tools():
    """Retrieves tools for interacting with the environment."""
    client = MultiServerMCPClient(
        {
            "dolores": {
                "transport": "http",
                "url": TOOLS_ENDPOINT,
            }
        }
    )
    return await client.get_tools()


async def evaluate_repository(agent: CompiledStateGraph, repository: str) -> None:
    """Evaluates a repository's pull requests and extracts durable security insights."""
    content = dedent(f"""
        Evaluate the {repository} repository for security vulnerabilities.

        Start by using check_semantic_memory to recall what you already know about {repository}.

        Use list_files to get the full list of files in the repository. Then use read_file to read and evaluate each file for security vulnerabilities. Focus on:
        * Hardcoded secrets, credentials, or tokens
        * Insecure dependencies or outdated packages
        * Injection vulnerabilities (SQL, command, path traversal)
        * Insecure authentication or authorization patterns
        * Sensitive data exposure
        * Misconfigured security controls

        Also use get_pull_requests and get_pull_request_status to understand the PR history. Analyze PRs to identify:
        * Successful vulnerability fixes and implementation patterns in merged PRs
        * Unresolved security concerns and rejected approaches in open and closed PRs
        * Patterns in how maintainers respond to security changes

        If you find vulnerabilities that require fixes:
        * Use git_clone to clone the repository
        * Use git_branch to create a branch
        * Use write_file to apply fixes to affected files
        * Use git_push to commit and push your changes with a descriptive message

        If no fixes are needed, do not create a branch or push changes.

        Before saving insights, check semantic_memory to see if similar insights already exist. Update or refine existing knowledge instead of creating duplicates.

        Use update_semantic_memory to save only actionable, specific insights that will improve future behavior.
    """)
    results = await agent.ainvoke(
        input={"messages": [HumanMessage(content=content)]},
        config={
            "configurable": {
                "thread_id": f"evaluate-{repository}",
            }
        },
        context=Context(repository=repository),
    )
    for message in results["messages"]:
        if (message.type == "ai") or (message.type == "tool"):
            print(dumps(message.model_dump()))


async def main():
    """Starts Dolores."""
    memory_tools = [
        update_procedural_memory,
        check_procedural_memory,
        update_semantic_memory,
        check_semantic_memory,
    ]
    environment_tools = await get_environment_tools()
    agent = create_agent(
        model=build_model_client(),
        tools=memory_tools + environment_tools,
        system_prompt=SYSTEM_PROMPT,
        context_schema=Context,
        checkpointer=DjangoCheckpointSaver(),
        store=DjangoStore(),
    )

    for repository in [repo.strip() for repo in REPOSITORIES.split(",")]:
        await evaluate_repository(agent, repository)


if __name__ == "__main__":
    run(main())
