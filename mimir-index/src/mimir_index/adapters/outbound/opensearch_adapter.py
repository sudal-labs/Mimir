"""VectorStore 구현체 — OpenSearch k-NN 벡터 + 키워드 하이브리드 인덱스."""
import os

from opensearchpy import AsyncOpenSearch

from mimir_index.domain.models import NoteChunk
from mimir_index.ports.outbound import VectorStore

INDEX_NAME = "mimir-notes"
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))


class OpenSearchAdapter(VectorStore):
    """opensearch-py AsyncOpenSearch 클라이언트로 청크를 upsert/delete한다."""

    def __init__(self, host: str, port: int) -> None:
        self._client = AsyncOpenSearch(hosts=[{"host": host, "port": port}])
        self._index_ready = False

    async def upsert_chunks(self, chunks: list[NoteChunk]) -> None:
        """청크 목록을 OpenSearch에 색인한다. 인덱스가 없으면 먼저 생성한다."""
        await self._ensure_index()
        for chunk in chunks:
            await self._client.index(
                index=INDEX_NAME,
                id=chunk.chunk_id,
                body={
                    "noteId": chunk.note_id,
                    "chunkIndex": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                },
            )

    async def delete_by_note_id(self, note_id: str) -> None:
        """특정 note_id와 연결된 청크를 모두 삭제한다."""
        await self._client.delete_by_query(
            index=INDEX_NAME,
            body={"query": {"term": {"noteId.keyword": note_id}}},
        )

    async def _ensure_index(self) -> None:
        """인덱스가 없으면 k-NN 매핑과 함께 생성한다."""
        if self._index_ready:
            return
        exists = await self._client.indices.exists(index=INDEX_NAME)
        if not exists:
            await self._client.indices.create(
                index=INDEX_NAME,
                body={
                    "settings": {"index": {"knn": True}},
                    "mappings": {
                        "properties": {
                            "noteId": {"type": "keyword"},
                            "chunkIndex": {"type": "integer"},
                            "content": {"type": "text", "analyzer": "standard"},
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": EMBEDDING_DIM,
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "nmslib",
                                },
                            },
                        }
                    },
                },
            )
        self._index_ready = True
