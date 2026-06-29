"""EventPublisher 구현체 — aiokafka를 통해 NoteChangedEvent를 Kafka에 발행한다."""
import json

from aiokafka import AIOKafkaProducer

from mimir_ingest.domain.models import NoteChangedEvent
from mimir_ingest.ports.outbound import EventPublisher

TOPIC_NOTE_CHANGED = "mimir.note.changed"


class KafkaEventPublisher(EventPublisher):
    """aiokafka AIOKafkaProducer로 NoteChangedEvent를 직렬화해 Kafka에 발행한다.

    start()/stop()은 FastAPI lifespan에서 호출한다.
    """

    def __init__(
            self,
            bootstrap_servers: str
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Kafka 프로듀서를 시작한다. 애플리케이션 시작 시 한 번 호출한다."""
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        """Kafka 프로듀서를 종료한다. 애플리케이션 종료 시 호출한다."""
        if self._producer:
            await self._producer.stop()

    async def publish(
            self,
            event: NoteChangedEvent
    ) -> None:
        """NoteChangedEvent를 JSON으로 직렬화해 Kafka에 발행한다.

        Kafka JSON 페이로드는 API 컨벤션에 따라 camelCase 키를 사용한다.
        키: event.note_id (파티션 라우팅용)
        """
        if not self._producer:
            raise RuntimeError("KafkaEventPublisher가 시작되지 않았습니다. start()를 먼저 호출하세요.")

        payload = {
            "noteId": event.note_id,
            "filePath": event.file_path,
            "changeType": event.change_type,
            "content": event.content,
            "frontmatter": {
                "tags": event.frontmatter.tags,
                "project": event.frontmatter.project,
                "date": event.frontmatter.date,
                "status": event.frontmatter.status,
                "extra": event.frontmatter.extra,
            },
            "commitHash": event.commit_hash,
            "occurredAt": event.occurred_at.isoformat(),
        }

        await self._producer.send_and_wait(
            TOPIC_NOTE_CHANGED,
            value=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            key=event.note_id.encode("utf-8"),
        )
