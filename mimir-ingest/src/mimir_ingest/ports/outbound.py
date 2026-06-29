"""mimir-ingest 아웃바운드 포트 — 애플리케이션에서 외부로 나가는 인터페이스"""
from abc import ABC, abstractmethod

from mimir_ingest.domain.models import NoteChangedEvent


class EventPublisher(ABC):
    """이벤트 버스(Kafka)에 NoteChangedEvent를 발행하는 아웃바운드 포트

    구현체: KafkaEventPublisher (adapters/outbound/kafka_producer.py)
    """

    @abstractmethod
    async def publish(
            self,
            event: NoteChangedEvent
    ) -> None:
        """단일 NoteChangedEvent를 이벤트 버스에 발행한다."""
        ...


class VaultReader(ABC):
    """git 저장소에서 커밋 간 diff와 파일 내용을 읽는 아웃바운드 포트

    구현체: GitVaultReader (adapters/outbound/git_reader.py)
    """

    @abstractmethod
    def get_diff(
        self,
        repo_path: str,
        before_hash: str,
        after_hash: str,
    ) -> list[tuple[str, str, str]]:
        """커밋 범위의 변경 파일 목록을 반환한다.

        Returns:
            (file_path, change_type, content) 튜플 리스트
            - file_path: 저장소 루트 기준 상대 경로
            - change_type: 'added' | 'modified' | 'deleted'
            - content: 변경 후 파일 내용 (deleted이면 '')
        """
        ...
