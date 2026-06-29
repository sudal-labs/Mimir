"""IngestUseCase 구현체 — VaultReader와 EventPublisher를 조합해 파이프라인을 실행한다"""
from datetime import datetime
from zoneinfo import ZoneInfo

import frontmatter

from mimir_ingest.domain.models import FrontmatterData, NoteChangedEvent
from mimir_ingest.ports.inbound import IngestUseCase
from mimir_ingest.ports.outbound import EventPublisher, VaultReader

SEOUL_TZ = ZoneInfo("Asia/Seoul")
MARKDOWN_EXTENSIONS: frozenset[str] = frozenset({".md", ".markdown"})


class IngestService(IngestUseCase):
    """git diff를 파싱하고 마크다운 노트만 필터링해 NoteChangedEvent를 발행한다."""

    def __init__(
            self,
            vault_reader: VaultReader,
            event_publisher: EventPublisher
    ) -> None:
        self._vault_reader = vault_reader
        self._event_publisher = event_publisher

    async def handle_git_push(
        self,
        repo_path: str,
        before_hash: str,
        after_hash: str,
    ) -> list[NoteChangedEvent]:
        """vault diff에서 마크다운 파일만 추출해 이벤트를 발행하고 목록을 반환한다."""
        raw_diffs = self._vault_reader.get_diff(repo_path, before_hash, after_hash)
        events: list[NoteChangedEvent] = []

        for file_path, change_type, content in raw_diffs:
            if not self._is_markdown(file_path):
                continue

            event = NoteChangedEvent(
                note_id=self._derive_note_id(file_path),
                file_path=file_path,
                change_type=change_type,
                content=content,
                frontmatter=self._parse_frontmatter(content),
                commit_hash=after_hash,
                occurred_at=datetime.now(tz=SEOUL_TZ),
            )
            await self._event_publisher.publish(event)
            events.append(event)

        return events

    # ── private helpers ──────────────────────────────────────────────

    def _is_markdown(
            self,
            file_path: str
    ) -> bool:
        """파일 경로가 마크다운 확장자인지 확인한다."""
        return any(file_path.endswith(ext) for ext in MARKDOWN_EXTENSIONS)

    def _parse_frontmatter(
            self,
            content: str
    ) -> FrontmatterData:
        """python-frontmatter로 YAML 헤더를 파싱한다. 실패 시 빈 FrontmatterData 반환."""
        if not content.strip():
            return FrontmatterData()
        try:
            post = frontmatter.loads(content)
            meta = post.metadata
            return FrontmatterData(
                tags=list(meta.get("tags") or []),
                project=str(meta.get("project", "")),
                date=str(meta.get("date", "")),
                status=str(meta.get("status", "")),
                extra={k: v for k, v in meta.items() if k not in ("tags", "project", "date", "status")},
            )
        except Exception:
            return FrontmatterData()

    def _derive_note_id(self, file_path: str) -> str:
        """파일 경로에서 슬러그 형태의 note_id를 생성한다.

        Example:
            'projects/mimir/design.md' → 'projects_mimir_design_md'
        """
        return file_path.replace("/", "_").replace(".", "_").lower()
