"""Kafka NoteChangedEvent 소비자 — mimir.note.changed 토픽을 구독한다."""
import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaConsumer

from mimir_link.ports.inbound import LinkUseCase

TOPIC_NOTE_CHANGED = "mimir.note.changed"
GROUP_ID = "mimir-link"

logger = logging.getLogger(__name__)


class KafkaLinkConsumer:
    """NoteChangedEvent를 소비해 LinkUseCase에 전달한다."""

    def __init__(self, link_use_case: LinkUseCase) -> None:
        self._link_use_case = link_use_case
        self._bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def start(self) -> None:
        """Kafka 소비 루프를 시작한다."""
        consumer = AIOKafkaConsumer(
            TOPIC_NOTE_CHANGED,
            bootstrap_servers=self._bootstrap_servers,
            group_id=GROUP_ID,
            value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await consumer.start()
        logger.info("mimir-link Kafka 소비자 시작: topic=%s, group=%s", TOPIC_NOTE_CHANGED, GROUP_ID)

        try:
            async for message in consumer:
                await self._process_message(message.value)
        finally:
            await consumer.stop()

    async def _process_message(self, event: dict[str, Any]) -> None:
        note_id = event.get("noteId", "unknown")
        try:
            await self._link_use_case.suggest_and_commit_links(event)
            logger.info("backlink 처리 완료: noteId=%s", note_id)
        except Exception:
            logger.exception("backlink 처리 실패: noteId=%s", note_id)
