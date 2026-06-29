# Third party imports.
from langchain.tools import tool, ToolRuntime

# Local imports.
from dolores.memory.context_schema import ContextSchema


@tool
async def check_semantic_memory(env: ToolRuntime[ContextSchema]) -> str:
    """Retrieves semantic facts about the current repository from memory."""
    namespace = ("semantic", env.context.repository)
    memories = await env.store.asearch(namespace, limit=100)
    if not memories:
        return None
    return "\n".join(memory.value["fact"] for memory in memories)


@tool
async def update_semantic_memory(env: ToolRuntime[ContextSchema], fact: str) -> str:
    """Saves a semantic fact about the current repository to memory."""
    namespace = ("semantic", env.context.repository)
    key = f"fact-{fact[:32].replace(' ', '-').lower()}"
    value = {"fact": fact}
    await env.store.aput(namespace, key, value)
    return f"Saved: {fact}"


@tool
async def check_procedural_memory(env: ToolRuntime[ContextSchema]) -> str:
    """Retrieves procedural instructions from memory."""
    namespace = ("procedural", "dolores")
    memories = await env.store.asearch(namespace, limit=100)
    if not memories:
        return None
    return "\n".join(memory.value["instruction"] for memory in memories)


@tool
async def update_procedural_memory(
    env: ToolRuntime[ContextSchema], instruction: str
) -> str:
    """Saves a procedural instruction to memory."""
    namespace = ("procedural", "dolores")
    key = f"procedure-{instruction[:32].replace(' ', '-').lower()}"
    value = {"instruction": instruction}
    await env.store.aput(namespace, key, value)
    return f"Saved: {instruction}"


def get_memory_tools() -> list:
    """Returns a list of memory tools."""
    return [
        check_procedural_memory,
        check_semantic_memory,
        update_procedural_memory,
        update_semantic_memory,
    ]
