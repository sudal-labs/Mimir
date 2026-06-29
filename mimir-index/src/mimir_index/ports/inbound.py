"""mimir-index 인바운드 포트"""
from abc import ABC, abstractmethod
from typing import Any


class IndexUseCase(ABC):
    """
    NoteChangedEvent를 받아 청킹·임베딩·저장을 수행하는 인바운드 포트

    구현체: IndexService (services/index_service.py)
    호출자: KafkaIndexConsumer (adapters/inbound/kafka_consumer.py)
    """

    @abstractmethod
    async def index_note(
            self,
            event: dict[str, Any]
    ) -> None:
        """
        NoteChangedEvent JSON dict를 받아 인덱싱 파이프라인을 실행한다.

        Args:
            event: Kafka에서 역직렬화한 NoteChangedEvent dict (camelCase 키)
        """
        ...
