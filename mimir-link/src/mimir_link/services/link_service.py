"""LinkUseCase 구현체 — 유사 노트 검색 → LLM 제안 → backlink 커밋."""
from typing import Any

from mimir_link.domain.models import BacklinkEntry
from mimir_link.ports.inbound import LinkUseCase
from mimir_link.ports.outbound import LlmLinkClient, SimilaritySearcher, VaultWriter

SIMILARITY_TOP_K = 5


class LinkService(LinkUseCase):
    """NoteChangedEvent에서 유사 노트를 찾고 LLM 제안 결과를 vault에 커밋한다."""

    def __init__(
        self,
        similarity_searcher: SimilaritySearcher,
        llm_link_client: LlmLinkClient,
        vault_writer: VaultWriter,
    ) -> None:
        self._similarity_searcher = similarity_searcher
        self._llm_link_client = llm_link_client
        self._vault_writer = vault_writer

    async def suggest_and_commit_links(self, event: dict[str, Any]) -> None:
        """deleted 이벤트는 스킵, added/modified는 링크 파이프라인을 실행한다."""
        if event.get("changeType") == "deleted":
            return

        note_id = event["noteId"]
        file_path = event.get("filePath", "")
        content = event.get("content", "")

        candidates = await self._similarity_searcher.find_similar_notes(
            note_id=note_id,
            content=content,
            top_k=SIMILARITY_TOP_K,
        )
        if not candidates:
            return

        suggestions = await self._llm_link_client.suggest_links(
            source_content=content,
            candidate_notes=candidates,
        )
        if not suggestions:
            return

        for suggestion in suggestions:
            suggestion.source_note_id = note_id

        related_note_ids = [s.target_note_id for s in suggestions]
        self._vault_writer.write_backlinks(BacklinkEntry(
            note_id=note_id,
            file_path=file_path,
            related_note_ids=related_note_ids,
        ))
