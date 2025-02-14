from langchain_community.document_loaders import WebBaseLoader


def get_web_base_loader(urls):
    loader = WebBaseLoader(urls)
    return loader.load()
