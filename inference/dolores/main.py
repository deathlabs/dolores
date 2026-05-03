# Third party imports.
from langchain.agents import create_agent
from langchain.messages import HumanMessage

# Local imports.
from dolores.tools.osint import convert_cve_to_stix, search_nvd

# Define the tools the agent can use.
tools = [convert_cve_to_stix, search_nvd]

# Create the agent.
agent = create_agent(
    model="openai:gpt-4o",
    system_prompt="You are a helpful assistant tasked with searching for CVEs and generating STIX 2.1 Vulnerability objects.",
    tools=tools,
)


def main():
    """Start the Dolores agent."""

    # Get the user prompt.
    user_prompt = "Generate a STIX object for the latest CVE regarding Django."
    user_message = [HumanMessage(content=user_prompt)]

    # Invoke the agent.
    agent_responses = agent.invoke({"messages": user_message})

    # Return the agent's response.
    for agent_response in agent_responses["messages"]:
        print(agent_response)


if __name__ == "__main__":
    main()
