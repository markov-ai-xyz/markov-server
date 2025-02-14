from langchain_community.tools.tavily_search import TavilySearchResults


def get_tavily_search(api_wrapper):
    return TavilySearchResults(api_wrapper=api_wrapper)
