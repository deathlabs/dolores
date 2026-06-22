# Standard library imports.
from contextlib import asynccontextmanager
from os import environ

# Third party imports.
from fastapi import FastAPI, Request
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from pydantic import BaseModel

# Local imports.
from dolores.checkpoint_saver import DjangoCheckpointSaver
from dolores.model_providers.openai import (
    get_openai_model,
    get_openai_model_from_azure,
)

# Get environment variables.
MODEL_PROVIDER = environ["MODEL_PROVIDER"]
TOOLS_ENDPOINT = environ["TOOLS_ENDPOINT"]

# Get a model handler.
match MODEL_PROVIDER:
    case "openai":
        model = get_openai_model()
    case "azure_openai":
        model = get_openai_model_from_azure()
    case _:
        print("Invalid MODEL_PROVIDER (options: openai or azure_openai).")
        exit(1)


# Identify the tools the agent has available.
async def get_tools():
    return await MultiServerMCPClient(
        {
            "dolores": {
                "transport": "http",
                "url": TOOLS_ENDPOINT,
            }
        }
    ).get_tools()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tools = await get_tools()
    app.state.agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant.",
        checkpointer=DjangoCheckpointSaver(),
        tools=tools,
    )
    yield


# Init a FastAPI server with the lifespan wired in directly.
api = FastAPI(lifespan=lifespan)


class InvokeRequest(BaseModel):
    thread_id: str
    message: str


@api.post("/invoke")
async def invoke(request: Request, body: InvokeRequest):
    agent = request.app.state.agent
    config = {"configurable": {"thread_id": body.thread_id}}
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": body.message}]},
        config=config,
    )
    return {"messages": result["messages"]}
