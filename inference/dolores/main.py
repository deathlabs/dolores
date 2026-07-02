# Standard library imports.
from asyncio import run
from json import dumps
from os import environ

# Third party imports.
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain.messages import HumanMessage

# Local imports.
from dolores.memory.context_schema import ContextSchema
from dolores.memory.long_term import DjangoStore
from dolores.memory.short_term import DjangoCheckpointSaver
from dolores.models import get_model_client
from dolores.prompts.system_prompts import get_evaluator_system_prompt
from dolores.prompts.user_prompts import get_evaluator_user_prompt
from dolores.tools import get_environment_tools, get_memory_tools

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]
REPOSITORIES = environ["REPOSITORIES"]


async def evaluate_repository(agent: CompiledStateGraph, repository: str) -> None:
    """Evaluates a repository's pull requests and extracts durable security insights."""
    user_prompt = get_evaluator_user_prompt(repository=repository)
    results = await agent.ainvoke(
        input={"messages": [HumanMessage(content=user_prompt)]},
        config={
            "configurable": {
                "thread_id": f"evaluate-{repository}",
            }
        },
        context=ContextSchema(repository=repository),
    )
    for message in results["messages"]:
        if (message.type == "ai") or (message.type == "tool"):
            print(dumps(message.model_dump()))


async def main():
    """Starts Dolores."""
    memory_tools = get_memory_tools()
    environment_tools = await get_environment_tools(url=TOOLS_ENDPOINT)
    agent = create_agent(
        model=get_model_client(model_provider=MODEL_PROVIDER),
        tools=memory_tools + environment_tools,
        system_prompt=get_evaluator_system_prompt(),
        context_schema=ContextSchema,
        checkpointer=DjangoCheckpointSaver(),
        store=DjangoStore(),
    )

    for repository in [repo.strip() for repo in REPOSITORIES.split(",")]:
        await evaluate_repository(agent, repository)


if __name__ == "__main__":
    run(main())
