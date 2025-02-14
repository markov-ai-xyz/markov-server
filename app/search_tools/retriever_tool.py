from langchain.tools.retriever import create_retriever_tool


def get_retriever_tool(retriever, name, description):
    return create_retriever_tool(retriever, name, description)
