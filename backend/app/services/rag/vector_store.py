from pathlib import Path

import chromadb

from app.services.rag.chunker import DocumentChunk


class VectorStore:
    """
    Persistent vector store for tender-document chunks.

    ChromaDB stores chunk text, embeddings, and metadata
    required for semantic retrieval and source tracing.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "tender_documents",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        Path(persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=persist_directory,
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description": (
                        "BidSure AI tender document "
                        "knowledge base"
                    )
                },
            )
        )

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match "
                "number of embeddings."
            )

        if not chunks:
            return

        self.collection.upsert(
            ids=[
                chunk.chunk_id
                for chunk in chunks
            ],
            documents=[
                chunk.text
                for chunk in chunks
            ],
            embeddings=embeddings,
            metadatas=[
                {
                    "source_document": (
                        chunk.source_document
                    ),
                    "chunk_index": (
                        chunk.chunk_index
                    ),
                }
                for chunk in chunks
            ],
        )

    def count(self) -> int:
        return self.collection.count()

    def delete(
        self,
        chunk_ids: list[str],
    ) -> None:

        if not chunk_ids:
            return

        self.collection.delete(
            ids=chunk_ids,
        )

vector_store = VectorStore()