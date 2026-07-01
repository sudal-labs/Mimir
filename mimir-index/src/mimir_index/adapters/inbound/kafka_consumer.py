"""Kafka NoteChangedEvent 소비자 — mimir.note.changed 토픽을 구독한다."""
import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaConsumer

from mimir_index.ports.inbound import IndexUseCase

TOPIC_NOTE_CHANGED = "mimir.note.changed"
GROUP_ID = "mimir-index"

logger = logging.getLogger(__name__)


class KafkaIndexConsumer:
    """NoteChangedEvent를 Kafka에서 소비해 IndexUseCase에 전달한다."""

    def __init__(self, index_use_case: IndexUseCase) -> None:
        self._index_use_case = index_use_case
        self._bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def start(self) -> None:
        """Kafka 소비 루프를 시작한다. 종료 시그널을 받을 때까지 블로킹된다."""
        consumer = AIOKafkaConsumer(
            TOPIC_NOTE_CHANGED,
            bootstrap_servers=self._bootstrap_servers,
            group_id=GROUP_ID,
            value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await consumer.start()
        logger.info("mimir-index Kafka 소비자 시작: topic=%s, group=%s", TOPIC_NOTE_CHANGED, GROUP_ID)

        try:
            async for message in consumer:
                await self._process_message(message.value)
        finally:
            await consumer.stop()

    async def _process_message(self, event: dict[str, Any]) -> None:
        """단일 이벤트를 IndexUseCase에 위임한다. 실패 시 로그 후 계속 진행한다."""
        note_id = event.get("noteId", "unknown")
        try:
            await self._index_use_case.index_note(event)
            logger.info("인덱싱 완료: noteId=%s", note_id)
        except Exception:
            logger.exception("인덱싱 실패: noteId=%s", note_id)
