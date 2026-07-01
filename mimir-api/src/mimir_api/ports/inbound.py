"""mimir-api 인바운드 포트."""
from abc import ABC, abstractmethod

from mimir_api.domain.models import NoteDetail, SearchResponse


class QueryUseCase(ABC):
    """vault를 검색하고 LLM으로 답변을 합성하는 인바운드 포트.

    구현체: QueryService (services/query_service.py)
    호출자:
        - REST API 라우터 (adapters/inbound/router.py)
        - MCP 서버 (adapters/inbound/mcp_server.py)
    """

    @abstractmethod
    async def search_notes(self, query: str, top_k: int = 5) -> SearchResponse:
        """질문을 하이브리드 검색하고 LLM으로 합성된 답변을 반환한다."""
        ...

    @abstractmethod
    async def get_note(self, note_id: str) -> NoteDetail | None:
        """note_id로 단일 노트를 조회한다. 없으면 None."""
        ...

    @abstractmethod
    async def suggest_links(self, note_id: str) -> list[str]:
        """note_id와 연관된 노트 ID 목록을 반환한다."""
        ...
