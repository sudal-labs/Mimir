"""mimir-index 아웃바운드 포트"""
from abc import ABC, abstractmethod

from mimir_index.domain.models import NoteChunk, NoteMetadata


class EmbeddingGenerator(ABC):
    """
    텍스트 청크를 임베딩 벡터로 변환하는 아웃바운드 포트

    구현체: SentenceTransformerEmbedding (adapters/outbound/ — 구현 예정)
    """

    @abstractmethod
    def generate_embeddings(
            self,
            texts: list[str]
    ) -> list[list[float]]:
        """texts를 배치로 임베딩 벡터 리스트로 변환한다."""
        ...


class VectorStore(ABC):
    """
    임베딩된 청크를 벡터+키워드 인덱스에 저장하는 아웃바운드 포트

    구현체: OpenSearchAdapter (adapters/outbound/opensearch_adapter.py)
    """

    @abstractmethod
    async def upsert_chunks(
            self,
            chunks: list[NoteChunk]
    ) -> None:
        """청크를 OpenSearch에 색인(upsert)"""
        ...

    @abstractmethod
    async def delete_by_note_id(
            self,
            note_id: str
    ) -> None:
        """특정 note_id의 모든 청크 삭제"""
        ...


class MetadataStore(ABC):
    """
    노트 메타데이터를 PostgreSQL에 저장하는 아웃바운드 포트

    구현체: PostgresAdapter (adapters/outbound/postgres_adapter.py)
    """

    @abstractmethod
    async def upsert_metadata(
            self,
            metadata: NoteMetadata
    ) -> None:
        """노트 메타데이터를 저장 또는 갱신"""
        ...

    @abstractmethod
    async def delete_by_note_id(
            self,
            note_id: str
    ) -> None:
        """특정 note_id의 메타데이터 삭제"""
        ...
