"""mimir-api 아웃바운드 포트."""
from abc import ABC, abstractmethod

from mimir_api.domain.models import NoteDetail, NoteRef


class HybridSearcher(ABC):
    """OpenSearch 하이브리드 검색 아웃바운드 포트."""

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[NoteRef]:
        """벡터 + 키워드 하이브리드 검색으로 관련 청크를 반환한다."""
        ...

    @abstractmethod
    async def get_note(self, note_id: str) -> NoteDetail | None:
        """note_id로 노트 상세 정보를 조회한다."""
        ...


class LlmSynthesizer(ABC):
    """검색 결과와 질문을 LLM에 보내 합성 답변을 생성하는 포트."""

    @abstractmethod
    async def synthesize(self, query: str, contexts: list[NoteRef]) -> str:
        """검색된 노트 컨텍스트를 기반으로 질문에 대한 답변을 합성한다."""
        ...
