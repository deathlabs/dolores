# Third party imports.
from langgraph.graph import StateGraph, MessagesState, START, END


# Invoke an LLM.
def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}


# The main entrypoint for the Dolores inference service.
def main():
    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    graph = graph.compile()
    result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    print(result)


if __name__ == "__main__":
    main()
