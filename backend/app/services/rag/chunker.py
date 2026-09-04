from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    """
    Represents a chunk of document text prepared for
    embedding and vector storage.
    """

    chunk_id: str
    text: str
    source_document: str
    chunk_index: int


class DocumentChunker:
    """
    Splits extracted document text into overlapping chunks.

    The chunker is intentionally independent of embeddings,
    vector databases, and LLM providers.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(
        self,
        text: str,
        source_document: str,
    ) -> list[DocumentChunk]:
        """
        Split document text into overlapping chunks.
        """

        if not text or not text.strip():
            return []

        normalized_text = " ".join(
            text.split()
        )

        chunks: list[DocumentChunk] = []

        start = 0
        chunk_index = 0

        step = (
            self.chunk_size
            - self.chunk_overlap
        )

        while start < len(normalized_text):

            end = min(
                start + self.chunk_size,
                len(normalized_text),
            )

            chunk_text = normalized_text[
                start:end
            ].strip()

            if chunk_text:

                chunks.append(
                    DocumentChunk(
                        chunk_id=(
                            f"{source_document}"
                            f":chunk:{chunk_index}"
                        ),
                        text=chunk_text,
                        source_document=source_document,
                        chunk_index=chunk_index,
                    )
                )

            if end >= len(normalized_text):
                break

            start += step
            chunk_index += 1

        return chunks


document_chunker = DocumentChunker()