"""IndexService 단위 테스트."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from mimir_index.services.index_service import IndexService


@pytest.fixture
def mock_embedding_generator():
    gen = MagicMock()
    gen.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
    return gen


@pytest.fixture
def mock_vector_store():
    return AsyncMock()


@pytest.fixture
def mock_metadata_store():
    return AsyncMock()


@pytest.fixture
def service(mock_embedding_generator, mock_vector_store, mock_metadata_store):
    return IndexService(
        embedding_generator=mock_embedding_generator,
        vector_store=mock_vector_store,
        metadata_store=mock_metadata_store,
    )


SAMPLE_EVENT = {
    "noteId": "projects_mimir_design_md",
    "filePath": "projects/mimir/design.md",
    "changeType": "added",
    "content": "# Design\n" + "내용입니다. " * 30,
    "frontmatter": {"tags": ["mimir"], "project": "mimir", "status": "draft"},
    "commitHash": "def456",
}


@pytest.mark.asyncio
async def test_index_note_upserts_chunks_and_metadata(service, mock_vector_store, mock_metadata_store):
    """added 이벤트 처리 시 VectorStore와 MetadataStore에 upsert가 호출되어야 한다."""
    await service.index_note(SAMPLE_EVENT)

    mock_vector_store.upsert_chunks.assert_awaited_once()
    mock_metadata_store.upsert_metadata.assert_awaited_once()

    saved_metadata = mock_metadata_store.upsert_metadata.call_args.args[0]
    assert saved_metadata.note_id == "projects_mimir_design_md"
    assert saved_metadata.tags == ["mimir"]


@pytest.mark.asyncio
async def test_index_note_deleted_event(service, mock_vector_store, mock_metadata_store):
    """deleted 이벤트는 VectorStore와 MetadataStore에 delete를 호출해야 한다."""
    event = {**SAMPLE_EVENT, "changeType": "deleted", "content": ""}
    await service.index_note(event)

    mock_vector_store.delete_by_note_id.assert_awaited_once_with("projects_mimir_design_md")
    mock_metadata_store.delete_by_note_id.assert_awaited_once_with("projects_mimir_design_md")
    mock_vector_store.upsert_chunks.assert_not_awaited()


def test_chunk_content_splits_correctly(service):
    """긴 텍스트는 여러 청크로 분할되어야 한다."""
    long_content = "A" * 1200
    chunks = service._chunk_content("note_1", long_content)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.note_id == "note_1"
        assert len(chunk.content) <= 500 + 10


def test_chunk_content_with_empty_string(service):
    """빈 내용은 청크가 0개여야 한다."""
    chunks = service._chunk_content("note_1", "")
    assert chunks == []
