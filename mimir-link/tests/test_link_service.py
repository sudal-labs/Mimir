"""LinkService 단위 테스트."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from mimir_link.domain.models import LinkSuggestion
from mimir_link.services.link_service import LinkService


@pytest.fixture
def mock_similarity_searcher():
    searcher = AsyncMock()
    searcher.find_similar_notes.return_value = [
        {"noteId": "note_b", "filePath": "b.md", "score": 0.92, "snippet": "내용 B"},
    ]
    return searcher


@pytest.fixture
def mock_llm_link_client():
    client = AsyncMock()
    client.suggest_links.return_value = [
        LinkSuggestion(
            source_note_id="",
            target_note_id="note_b",
            target_file_path="b.md",
            reason="두 노트가 같은 개념을 다룬다.",
            confidence=0.88,
        )
    ]
    return client


@pytest.fixture
def mock_vault_writer():
    return MagicMock()


@pytest.fixture
def service(mock_similarity_searcher, mock_llm_link_client, mock_vault_writer):
    return LinkService(
        similarity_searcher=mock_similarity_searcher,
        llm_link_client=mock_llm_link_client,
        vault_writer=mock_vault_writer,
    )


SAMPLE_EVENT = {
    "noteId": "note_a",
    "filePath": "a.md",
    "changeType": "added",
    "content": "# Note A\n내용입니다.",
}


@pytest.mark.asyncio
async def test_suggest_and_commit_links_calls_vault_writer(service, mock_vault_writer):
    """유사 노트가 있고 LLM이 제안하면 VaultWriter가 호출되어야 한다."""
    await service.suggest_and_commit_links(SAMPLE_EVENT)

    mock_vault_writer.write_backlinks.assert_called_once()
    entry = mock_vault_writer.write_backlinks.call_args.args[0]
    assert entry.note_id == "note_a"
    assert "note_b" in entry.related_note_ids


@pytest.mark.asyncio
async def test_deleted_event_is_skipped(service, mock_vault_writer):
    """changeType이 'deleted'인 이벤트는 처리를 건너뛴다."""
    event = {**SAMPLE_EVENT, "changeType": "deleted"}
    await service.suggest_and_commit_links(event)

    mock_vault_writer.write_backlinks.assert_not_called()


@pytest.mark.asyncio
async def test_no_candidates_skips_llm_and_writer(
    service, mock_similarity_searcher, mock_llm_link_client, mock_vault_writer
):
    """유사 노트가 없으면 LLM 호출과 커밋이 발생하지 않아야 한다."""
    mock_similarity_searcher.find_similar_notes.return_value = []
    await service.suggest_and_commit_links(SAMPLE_EVENT)

    mock_llm_link_client.suggest_links.assert_not_awaited()
    mock_vault_writer.write_backlinks.assert_not_called()
