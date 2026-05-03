# Standard library imports.
from typing import Literal

# Third party imports.
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import END, MessagesState, StateGraph, START, END

# Local imports.
from dolores.tools.math import add, multiply, divide

# Init the model.
model = init_chat_model("gpt-4o")

# Define the tools the model can use.
tools = [add, multiply, divide]

# Bind the tools to the model.
model_with_tools = model.bind_tools(tools)


def model_call_node(state: MessagesState) -> dict:
    """A node for calling the model."""

    # Create a system prompt for the model.
    system_prompt = "You are a helpful assistant tasked with performing arithmetic on a set of inputs."

    # Create a SystemMessage with the system prompt.
    system_message = SystemMessage(content=system_prompt)

    # Call the model.
    messages = [model_with_tools.invoke([system_message] + state["messages"])]

    # Return the model's output.
    return {"messages": messages}


def tool_call_node(state: dict) -> dict:
    """A node for calling tools selected by the model."""

    # Create a dictionary of tool names to make it easy to look up tools by name.
    tools_by_name = {tool.name: tool for tool in tools}

    # Init an empty list of tool messages to store the results of tool calls.
    tool_messages = []

    # For every tool call in the model's last message, perform the tool call.
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool corresponding to the tool selected by the model.
        tool = tools_by_name[tool_call["name"]]

        # Perform the tool call with the provided arguments.
        tool_call_result = tool.invoke(tool_call["args"])

        # Use the result of the tool call result to create a ToolMessage (include "id" so the model can map tool calls to tool call results).
        tool_message = ToolMessage(
            content=tool_call_result, tool_call_id=tool_call["id"]
        )

        # Add the tool message to the list of tool messages.
        tool_messages.append(tool_message)

    # Return the tool messages so the model can reflect on the results of its tool calls.
    return {"messages": tool_messages}


def should_continue(state: MessagesState) -> Literal["tool_call_node", END]:
    """A node for deciding if the current task being executed should continue or stop."""

    # Get the last message.
    last_message = state["messages"][-1]

    # If the model made a tool call in its last message, continue onto the tool node to perform the tool call.
    if last_message.tool_calls:
        return "tool_call_node"

    # Otherwise, stop.
    return END


# Init a graph.
graph = StateGraph(MessagesState)

# Add nodes to the graph.
graph.add_node("model_call_node", model_call_node)
graph.add_node("tool_call_node", tool_call_node)

# Connect the nodes within the graph by adding edges between them.
graph.add_edge(START, "model_call_node")
graph.add_conditional_edges("model_call_node", should_continue, ["tool_call_node", END])
graph.add_edge("tool_call_node", "model_call_node")

# Compile the graph.
agent = graph.compile()


def main():
    """Start the Dolores agent."""

    # Get the user prompt.
    user_prompt = "Add 3 and 4 over and over again until the sum becomes 100."

    # Create a list of messages starting with the user's prompt.
    user_message = [HumanMessage(content=user_prompt)]

    # Invoke the agent.
    agent_responses = agent.invoke({"messages": user_message})

    # Return the agent's response.
    for agent_response in agent_responses["messages"]:
        print(agent_response)


if __name__ == "__main__":
    main()
