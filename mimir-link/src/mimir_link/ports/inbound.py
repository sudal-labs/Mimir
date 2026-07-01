"""mimir-link 인바운드 포트."""
from abc import ABC, abstractmethod
from typing import Any


class LinkUseCase(ABC):
    """NoteChangedEvent를 받아 backlink 생성 파이프라인을 실행하는 인바운드 포트.

    구현체: LinkService (services/link_service.py)
    호출자: KafkaLinkConsumer (adapters/inbound/kafka_consumer.py)
    """

    @abstractmethod
    async def suggest_and_commit_links(self, event: dict[str, Any]) -> None:
        """NoteChangedEvent를 처리하고, LLM 제안 결과를 backlink로 vault에 커밋한다.

        Args:
            event: Kafka에서 역직렬화한 NoteChangedEvent dict (camelCase 키).
        """
        ...
