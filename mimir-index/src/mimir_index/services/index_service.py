"""IndexUseCase 구현체 — 청킹, 임베딩, 저장을 조합한다."""
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from mimir_index.domain.models import NoteChunk, NoteMetadata
from mimir_index.ports.inbound import IndexUseCase
from mimir_index.ports.outbound import EmbeddingGenerator, MetadataStore, VectorStore

SEOUL_TZ = ZoneInfo("Asia/Seoul")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))


class IndexService(IndexUseCase):
    """NoteChangedEvent를 받아 청킹 → 임베딩 → OpenSearch+PostgreSQL 저장을 수행한다."""

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
    ) -> None:
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._metadata_store = metadata_store

    async def index_note(self, event: dict[str, Any]) -> None:
        """NoteChangedEvent(camelCase JSON dict)를 처리한다.

        - 'deleted': 기존 인덱스 및 메타데이터 삭제.
        - 'added'/'modified': 청킹 → 임베딩 → upsert.
        """
        note_id = event["noteId"]
        change_type = event["changeType"]
        content = event.get("content", "")
        frontmatter = event.get("frontmatter", {})

        if change_type == "deleted":
            await self._vector_store.delete_by_note_id(note_id)
            await self._metadata_store.delete_by_note_id(note_id)
            return

        chunks = self._chunk_content(note_id, content)

        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedding_generator.generate_embeddings(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        await self._vector_store.upsert_chunks(chunks)
        await self._metadata_store.upsert_metadata(NoteMetadata(
            note_id=note_id,
            file_path=event.get("filePath", ""),
            tags=frontmatter.get("tags", []),
            project=frontmatter.get("project", ""),
            status=frontmatter.get("status", ""),
            commit_hash=event.get("commitHash", ""),
            indexed_at=datetime.now(tz=SEOUL_TZ),
        ))

    def _chunk_content(self, note_id: str, content: str) -> list[NoteChunk]:
        """텍스트를 고정 길이 슬라이딩 윈도우로 분할한다."""
        if not content.strip():
            return []

        chunks: list[NoteChunk] = []
        start = 0
        index = 0
        while start < len(content):
            end = start + CHUNK_SIZE
            chunk_text = content[start:end]
            chunks.append(NoteChunk(
                chunk_id=f"{note_id}_{index}",
                note_id=note_id,
                content=chunk_text,
                chunk_index=index,
            ))
            start = end - CHUNK_OVERLAP
            index += 1

        return chunks
