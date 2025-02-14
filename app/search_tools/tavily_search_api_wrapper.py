from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper


def get_tavily_search_api_wrapper(api_key):
    return TavilySearchAPIWrapper(tavily_api_key=api_key)
