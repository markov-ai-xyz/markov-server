from pinecone import Pinecone, ServerlessSpec, QueryResponse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from typing import List, Dict, Union, Tuple
from pathlib import Path
import time
import uuid


class PineconeLoader:
    def __init__(
        self,
        pinecone_api_key: str,
        index_name: str,
        openai_api_key: str,
        cloud: str = "aws",
        region: str = "us-east-1"
    ):
        self.index_name = index_name
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.pc = Pinecone(api_key=pinecone_api_key)

        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if index_name not in existing_indexes:
            self.pc.create_index(
                name=index_name,
                dimension=1536,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud=cloud,
                    region=region
                )
            )

        self.index = self.pc.Index(index_name)

    def create_embedding_for_text(self, text: str) -> Tuple[str, List[float], Dict]:
        embedding = self.embeddings.embed_documents([text])[0]
        vector_id = str(uuid.uuid4())
        metadata = {"text": text}

        return vector_id, embedding, metadata

    def _process_text_chunks(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

        chunks = text_splitter.split_text(text)

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = self.embeddings.embed_documents(batch)
            vectors = []

            for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                vector_id = str(uuid.uuid4())
                vectors.append((vector_id, embedding, {"text": chunk}))

            self.index.upsert(vectors=vectors)
            time.sleep(1)
            print(f"Processed chunks {i} to {i + len(batch)}")

    def process_file(self, file_path: Union[str, Path], chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        self._process_text_chunks(text, chunk_size, chunk_overlap)

    def process_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self._process_text_chunks(str(text), chunk_size, chunk_overlap)

    def search(self, query: str, top_k: int = 2) -> QueryResponse:
        query_embedding = self.embeddings.embed_query(query)

        return self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
