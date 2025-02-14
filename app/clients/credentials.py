EREKRUT_API_KEY = "mdp-erekrut"
BROWN_LIVING_API_KEY = "mdp-brown-living"
MARKOV_AI_API_KEY = "mdp-markov-ai"

CLIENT_CREDENTIALS = {
    BROWN_LIVING_API_KEY: {
        "COLLECTION_NAME": "brown_living",
        "RETRIEVER_TOOL_NAME": "brown_living_retriever",
        "HUB": "anant-chandra/helpful-assistant",
        "PROMPT": "Search for information about planet positivity, sustainable brands, everyday-use products, and Brown Living. For any questions about those topics, you must use this tool! Try to answer in no more than 2-3 sentences unless specifically asked for a detailed answer.",
    },
    MARKOV_AI_API_KEY: {
        "COLLECTION_NAME": "markov_ai",
        "RETRIEVER_TOOL_NAME": "markov_ai_retriever",
        "HUB": "anant-chandra/helpful-assistant",
        "PROMPT": "Search for information about Markov AI. For any questions about those topics, you must use this tool! Try to answer in no more than 2-3 sentences unless specifically asked for a detailed answer.",
    },
}

WHITELISTED_API_KEYS = [EREKRUT_API_KEY, BROWN_LIVING_API_KEY, MARKOV_AI_API_KEY]
