"""mimir-link 아웃바운드 포트."""
from abc import ABC, abstractmethod

from mimir_link.domain.models import BacklinkEntry, LinkSuggestion


class SimilaritySearcher(ABC):
    """OpenSearch에서 유사 노트를 검색하는 아웃바운드 포트."""

    @abstractmethod
    async def find_similar_notes(
        self,
        note_id: str,
        content: str,
        top_k: int = 5,
    ) -> list[dict]:
        """입력 content와 유사한 노트 목록을 반환한다.

        Returns:
            [{"noteId": ..., "filePath": ..., "score": ..., "snippet": ...}] 형태.
        """
        ...


class LlmLinkClient(ABC):
    """LLM(Claude/Grok)을 호출해 연결 제안을 생성하는 아웃바운드 포트."""

    @abstractmethod
    async def suggest_links(
        self,
        source_content: str,
        candidate_notes: list[dict],
    ) -> list[LinkSuggestion]:
        """source_content와 candidates 중 연결 가치가 있는 쌍을 제안한다."""
        ...


class VaultWriter(ABC):
    """vault 노트 파일에 backlink를 추가하고 git commit하는 아웃바운드 포트."""

    @abstractmethod
    def write_backlinks(self, entry: BacklinkEntry) -> None:
        """노트 파일의 frontmatter에 relatedNotes 필드를 추가/갱신하고 커밋한다."""
        ...
