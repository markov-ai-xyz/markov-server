from pymongo import MongoClient
from langchain_community.vectorstores import MongoDBAtlasVectorSearch


def get_mongo_exporter_instance(uri, db_name, collection_name, embeddings):
    client = MongoClient(uri)
    collection = client[db_name][collection_name]
    vectorstore = MongoDBAtlasVectorSearch(collection, embeddings)
    return vectorstore
