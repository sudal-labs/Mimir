"""mimir-ingest 인바운드 포트 — 외부에서 애플리케이션으로 들어오는 인터페이스"""
from abc import ABC, abstractmethod

from mimir_ingest.domain.models import NoteChangedEvent


class IngestUseCase(ABC):
    """git push 이벤트를 처리해 NoteChangedEvent 목록을 반환하는 인바운드 포트

    구현체: IngestService (services/ingest_service.py)
    호출자: webhook 라우터 (adapters/inbound/webhook.py)
    """

    @abstractmethod
    async def handle_git_push(
        self,
        repo_path: str,
        before_hash: str,
        after_hash: str,
    ) -> list[NoteChangedEvent]:
        """vault 저장소의 커밋 범위에서 변경된 노트를 추출하고 이벤트를 발행한다.

        Args:
            repo_path: vault git 저장소 로컬 경로
            before_hash: push 이전 HEAD 커밋 SHA
            after_hash: push 이후 HEAD 커밋 SHA

        Returns:
            발행된 NoteChangedEvent 목록
        """
        ...
