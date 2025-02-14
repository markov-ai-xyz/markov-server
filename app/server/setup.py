import os
from dotenv import load_dotenv
from app.embeddings.openai_embeddings import get_openai_embeddings
from app.retrievers.mongodb_atlas_vector_retriever import get_vector_retriever
from app.search_tools.retriever_tool import get_retriever_tool
from app.search_tools.tavily_search_api_wrapper import get_tavily_search_api_wrapper
from app.search_tools.tavily_search import get_tavily_search
from app.agents.openai_functions_agent import get_openai_functions_agent
from app.agents.agent_executor import get_agent_executor
from app.sql.db_config import create_tables

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
DB_NAME = os.getenv("DB_NAME")
ATLAS_VECTOR_SEARCH_INDEX_NAME = os.getenv("ATLAS_VECTOR_SEARCH_INDEX_NAME")


def create_retriever(collection):
    embeddings = get_openai_embeddings(OPENAI_API_KEY)
    qa_retriever = get_vector_retriever(
        MONGODB_ATLAS_CLUSTER_URI,
        DB_NAME,
        collection,
        ATLAS_VECTOR_SEARCH_INDEX_NAME,
        embeddings,
    )
    return qa_retriever


def create_tools(vector_retriever, retriever_tool_name, prompt):
    retriever_tool = get_retriever_tool(vector_retriever, retriever_tool_name, prompt)
    tavily_search_api_wrapper = get_tavily_search_api_wrapper(TAVILY_API_KEY)
    search = get_tavily_search(tavily_search_api_wrapper)
    return [retriever_tool, search]


def create_agent_executor(collection, retriever_tool_name, prompt, hub_link):
    retriever = create_retriever(collection)
    tools = create_tools(retriever, retriever_tool_name, prompt)
    agent = get_openai_functions_agent(tools, hub_link)
    agent_executor = get_agent_executor(agent, tools)
    return agent_executor


def create_rag_only_agent(collection, retriever_tool_name, prompt, hub_link):
    retriever = create_retriever(collection)
    retriever_tool = get_retriever_tool(retriever, retriever_tool_name, prompt)
    tools = [retriever_tool]
    agent = get_openai_functions_agent(tools, hub_link)
    agent_executor = get_agent_executor(agent, tools)
    return agent_executor


def create_sql_engine():
    create_tables()
