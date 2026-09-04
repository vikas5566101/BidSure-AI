from app.services.rag.embeddings import embedding_service
from app.services.rag.vector_store import vector_store


class RetrievalResult:
    """
    Represents one retrieved document chunk.
    """

    def __init__(
        self,
        chunk_id: str,
        text: str,
        source_document: str,
        chunk_index: int,
        distance: float,
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.source_document = source_document
        self.chunk_index = chunk_index
        self.distance = distance


class Retriever:
    """
    Performs semantic retrieval over indexed tender documents.
    """

    def __init__(
        self,
        store=vector_store,
        embeddings=embedding_service,
    ):
        self.store = store
        self.embeddings = embeddings

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_document: str | None = None,
    ) -> list[RetrievalResult]:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if source_document is not None and not source_document.strip():
            raise ValueError(
                "source_document cannot be empty."
            )

        if self.store.count() == 0:
            return []

        query_embedding = (
            self.embeddings.embed_text(query)
        )

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(
                top_k,
                self.store.count(),
            ),
        }

        if source_document:
            query_kwargs["where"] = {
                "source_document": source_document
            }

        results = self.store.collection.query(
            **query_kwargs
        )

        retrieved: list[RetrievalResult] = []

        ids = results.get("ids", [[]])[0]

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        for index, chunk_id in enumerate(ids):

            metadata = metadatas[index]

            retrieved.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=documents[index],
                    source_document=metadata[
                        "source_document"
                    ],
                    chunk_index=metadata[
                        "chunk_index"
                    ],
                    distance=distances[index],
                )
            )

        return retrieved


retriever = Retriever()