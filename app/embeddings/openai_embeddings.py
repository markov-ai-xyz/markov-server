from langchain_openai import OpenAIEmbeddings


def get_openai_embeddings(api_key):
    return OpenAIEmbeddings(api_key=api_key)
