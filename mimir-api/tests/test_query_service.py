"""QueryService 단위 테스트."""
import pytest
from unittest.mock import AsyncMock

from mimir_api.domain.models import NoteDetail, NoteRef, SearchResponse
from mimir_api.services.query_service import QueryService


@pytest.fixture
def mock_searcher():
    searcher = AsyncMock()
    searcher.search.return_value = [
        NoteRef(note_id="note_a", file_path="a.md", score=0.95, snippet="내용 A"),
    ]
    searcher.get_note.return_value = NoteDetail(
        note_id="note_a",
        file_path="a.md",
        content="# A\n내용",
        frontmatter={"tags": ["mimir"]},
        related_note_ids=["note_b"],
    )
    return searcher


@pytest.fixture
def mock_synthesizer():
    synthesizer = AsyncMock()
    synthesizer.synthesize.return_value = "LLM 합성 답변입니다."
    return synthesizer


@pytest.fixture
def service(mock_searcher, mock_synthesizer):
    return QueryService(searcher=mock_searcher, synthesizer=mock_synthesizer)


@pytest.mark.asyncio
async def test_search_notes_returns_answer(service):
    """검색 결과가 있을 때 LLM 합성 답변이 포함된 SearchResponse를 반환해야 한다."""
    response = await service.search_notes(query="mimir 설계", top_k=3)

    assert isinstance(response, SearchResponse)
    assert response.answer == "LLM 합성 답변입니다."
    assert len(response.source_notes) == 1
    assert response.source_notes[0].note_id == "note_a"


@pytest.mark.asyncio
async def test_search_notes_with_no_results(service, mock_searcher):
    """검색 결과가 없으면 '관련 노트를 찾을 수 없습니다.' 답변을 반환해야 한다."""
    mock_searcher.search.return_value = []
    response = await service.search_notes(query="없는 내용")

    assert "찾을 수 없습니다" in response.answer
    assert response.source_notes == []


@pytest.mark.asyncio
async def test_get_note_returns_detail(service):
    """존재하는 note_id 조회 시 NoteDetail을 반환해야 한다."""
    note = await service.get_note(note_id="note_a")

    assert note is not None
    assert note.note_id == "note_a"
    assert note.file_path == "a.md"


@pytest.mark.asyncio
async def test_get_note_returns_none_for_missing(service, mock_searcher):
    """존재하지 않는 note_id 조회 시 None을 반환해야 한다."""
    mock_searcher.get_note.return_value = None
    note = await service.get_note(note_id="missing_note")

    assert note is None


@pytest.mark.asyncio
async def test_suggest_links_returns_related_ids(service):
    """note_id의 연관 노트 ID 목록을 반환해야 한다."""
    related_ids = await service.suggest_links(note_id="note_a")

    assert related_ids == ["note_b"]
