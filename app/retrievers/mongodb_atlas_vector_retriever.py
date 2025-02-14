from pymongo import MongoClient
from langchain_community.vectorstores import MongoDBAtlasVectorSearch


def get_vector_retriever_for_supplied_documents(
    uri, db_name, collection_name, index_name, embeddings, documents
):
    client = MongoClient(uri)
    collection = client[db_name][collection_name]
    vector_search = MongoDBAtlasVectorSearch.from_documents(
        documents=documents,
        embedding=embeddings,
        collection=collection,
        index_name=index_name,
    )
    return vector_search.as_retriever(search_type="similarity", search_kwargs={"k": 15})


def get_vector_retriever(uri, db_name, collection_name, index_name, embeddings):
    vector_search = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=uri,
        namespace=f"{db_name}.{collection_name}",
        embedding=embeddings,
        index_name=index_name,
    )
    return vector_search.as_retriever(search_type="similarity", search_kwargs={"k": 15})
