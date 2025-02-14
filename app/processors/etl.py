# TODO: Deprecate this file and create processors per modality

from app.loggers.custom import logger
from typing import Iterable
from typing import List, Dict
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
import requests
import json
import tiktoken
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, disallowed_special=())
chat_model = ChatOpenAI(api_key=OPENAI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("markov")


def get_text_splitter(max_tokens: int = 1000, overlap_tokens: int = 100):
    return RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=overlap_tokens,
        length_function=get_token_count,
        separators=["\n\n", "\n", " ", ""],
    )


def get_token_count(text: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(encoding.encode(text))


def split_documents_to_chunks(documents: Iterable[Document]) -> List[Document]:
    text_splitter = get_text_splitter()
    chunks = []

    for doc in documents:
        if doc.metadata["type"] == "text":
            split_docs = text_splitter.split_documents([doc])
            chunks.extend(split_docs)
        elif doc.metadata["type"] == "image":
            chunks.append(doc)
        else:
            print(f"Unrecognized document type: {doc.metadata['type']}")

    return chunks


def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    try:
        return embeddings.embed_documents(chunks)
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise


def extract_relations(chunks: List[str]) -> List[Dict[str, str]]:
    try:
        prompt = f"""
        Given the following text chunks, identify the relations between them.
        Format the output as a list of dictionaries, each containing "source", "relation", and "target" keys.
        The "source" and "target" should be the index of the chunk (0-based), and "relation" should describe how they are related.

        Text chunks:
        {chunks}

        Relations:
        """
        response = chat_model.predict(prompt)
        relations = eval(response)
        return relations
    except Exception as e:
        logger.error(f"Error in relation extraction: {str(e)}")
        raise


def store_in_neo4j(
    driver: "Union[Neo4jDriver, NeptuneDriver]",
    chunks: List[str],
    relations: List[Dict[str, str]],
):
    try:
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:TextChunk) REQUIRE c.id IS UNIQUE"
            )

            for i, chunk in enumerate(chunks):
                session.run(
                    """
                    MERGE (c:TextChunk {id: $id})
                    SET c.text = $text
                """,
                    id=i,
                    text=chunk,
                )

            for relation in relations:
                session.run(
                    """
                    MATCH (source:TextChunk {id: $source_id})
                    MATCH (target:TextChunk {id: $target_id})
                    MERGE (source)-[r:RELATED_TO {relation: $relation}]->(target)
                """,
                    source_id=int(relation["source"]),
                    target_id=int(relation["target"]),
                    relation=relation["relation"],
                )

        logger.info("Data successfully stored in Neo4j")
    except Exception as e:
        logger.error(f"Error storing data in Neo4j: {str(e)}")
        raise


def process_and_store_text(
    driver: "Union[Neo4jDriver, NeptuneDriver]", chunks: List[str]
):
    try:
        relations = extract_relations(chunks)
        store_in_neo4j(driver, chunks, relations)
        logger.info("Text processing and storage completed successfully")

    except Exception as e:
        logger.error(f"Error in text processing pipeline: {str(e)}")


def send_chunks(chunks: str):
    data = {
        "input": chunks,
    }

    json_data = json.dumps(data)

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            "http://0.0.0.0:5001/relik", data=json_data, headers=headers
        )

        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful!")
            print(response.json())
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def process_and_store_documents(
    driver: "Union[Neo4jDriver, NeptuneDriver]", documents: Iterable[Document]
):
    try:
        chunks = split_documents_to_chunks(documents)
        image_chunks = []

        for chunk in chunks:
            if chunk.metadata and chunk.metadata["type"] == "image":
                image_chunks.append(chunk)
            elif chunk.metadata and chunk.metadata["type"] == "text":
                send_chunks(chunk.page_content)
            else:
                logger.warning(f"Unexpected chunk type: {type(chunk)}")

        if image_chunks:
            process_and_store_images(driver, image_chunks)

    except Exception as e:
        logger.error(f"Error in document processing pipeline: {str(e)}")


def process_and_store_images(driver, image_chunks):
    for chunk in image_chunks:
        try:
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this image thoroughly and provide a detailed description. Aim to be comprehensive yet concise, focusing on factual observations rather than subjective interpretations unless specifically relevant.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{chunk.metadata['image_format']};base64,{chunk.metadata['image_data']}",
                            "detail": "auto",
                        },
                    },
                ],
            }
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=[message], max_tokens=1000
            )
            image_description = response.choices[0].message.content

            # TODO Send image_description to relik, create graph and store in neo4j
            send_chunks(image_description)
            logger.info(
                f"Image from page {chunk.metadata['page']} processed successfully - {image_description}"
            )
        except Exception as e:
            logger.error(
                f"Error processing image from page {chunk.metadata['page']}: {str(e)}"
            )
