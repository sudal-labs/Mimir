"""MetadataStore 구현체 — SQLAlchemy로 PostgreSQL notes/chunks 테이블을 관리한다."""
import os

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mimir_index.adapters.outbound.postgres_models import ChunkModel, NoteModel
from mimir_index.domain.models import NoteChunk, NoteMetadata
from mimir_index.ports.outbound import MetadataStore


def build_database_url() -> str:
    """환경 변수로 asyncpg DSN을 구성한다."""
    user = os.getenv("POSTGRES_USER", "mimir")
    password = os.getenv("POSTGRES_PASSWORD", "mimir")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "mimir")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


class PostgresAdapter(MetadataStore):
    """AsyncSession 기반 PostgreSQL 메타데이터 저장소."""

    def __init__(self) -> None:
        engine = create_async_engine(build_database_url(), echo=False)
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def upsert_metadata(self, metadata: NoteMetadata) -> None:
        """노트 메타데이터를 삽입 또는 갱신한다."""
        async with self._session_factory() as session:
            async with session.begin():
                existing = await session.get(NoteModel, metadata.note_id)
                if existing:
                    existing.file_path = metadata.file_path
                    existing.tags = metadata.tags
                    existing.project = metadata.project
                    existing.status = metadata.status
                    existing.commit_hash = metadata.commit_hash
                    existing.indexed_at = metadata.indexed_at
                else:
                    session.add(NoteModel(
                        note_id=metadata.note_id,
                        file_path=metadata.file_path,
                        tags=metadata.tags,
                        project=metadata.project,
                        status=metadata.status,
                        commit_hash=metadata.commit_hash,
                        indexed_at=metadata.indexed_at,
                    ))

    async def delete_by_note_id(self, note_id: str) -> None:
        """특정 note_id의 노트 및 청크 메타데이터를 모두 삭제한다."""
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(delete(ChunkModel).where(ChunkModel.note_id == note_id))
                await session.execute(delete(NoteModel).where(NoteModel.note_id == note_id))

    async def upsert_chunk_metadata(self, chunks: list[NoteChunk]) -> None:
        """청크 메타데이터를 PostgreSQL에도 저장한다 (벡터 제외)."""
        async with self._session_factory() as session:
            async with session.begin():
                for chunk in chunks:
                    existing = await session.get(ChunkModel, chunk.chunk_id)
                    if existing:
                        existing.content = chunk.content
                    else:
                        session.add(ChunkModel(
                            chunk_id=chunk.chunk_id,
                            note_id=chunk.note_id,
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                        ))
