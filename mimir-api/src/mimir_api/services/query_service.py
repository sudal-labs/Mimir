"""QueryUseCase 구현체 — 검색 + LLM 합성을 조합한다."""
from mimir_api.domain.models import NoteDetail, SearchResponse
from mimir_api.ports.inbound import QueryUseCase
from mimir_api.ports.outbound import HybridSearcher, LlmSynthesizer


class QueryService(QueryUseCase):
    """하이브리드 검색 결과를 LLM으로 합성해 근거 링크 포함 답변을 생성한다."""

    def __init__(self, searcher: HybridSearcher, synthesizer: LlmSynthesizer) -> None:
        self._searcher = searcher
        self._synthesizer = synthesizer

    async def search_notes(self, query: str, top_k: int = 5) -> SearchResponse:
        """질문에 대해 하이브리드 검색 후 LLM 합성 답변을 반환한다."""
        note_refs = await self._searcher.search(query=query, top_k=top_k)
        if not note_refs:
            return SearchResponse(answer="관련 노트를 찾을 수 없습니다.", source_notes=[])

        answer = await self._synthesizer.synthesize(query=query, contexts=note_refs)
        return SearchResponse(answer=answer, source_notes=note_refs)

    async def get_note(self, note_id: str) -> NoteDetail | None:
        """단일 노트를 조회한다."""
        return await self._searcher.get_note(note_id=note_id)

    async def suggest_links(self, note_id: str) -> list[str]:
        """note_id와 연관된 노트 목록을 반환한다."""
        note = await self._searcher.get_note(note_id=note_id)
        if note is None:
            return []
        return note.related_note_ids
