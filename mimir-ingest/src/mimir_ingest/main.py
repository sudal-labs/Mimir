"""mimir-ingest FastAPI 애플리케이션 엔트리포인트"""
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from mimir_ingest.adapters.inbound import webhook
from mimir_ingest.adapters.inbound.webhook import router as webhook_router
from mimir_ingest.adapters.outbound.git_reader import GitVaultReader
from mimir_ingest.adapters.outbound.kafka_producer import KafkaEventPublisher
from mimir_ingest.services.ingest_service import IngestService

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

kafka_publisher = KafkaEventPublisher(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
vault_reader = GitVaultReader()
ingest_service = IngestService(vault_reader=vault_reader, event_publisher=kafka_publisher)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI 앱 라이프싸이클 — 시작 시 Kafka 연결, 종료 시 해제"""
    await kafka_publisher.start()
    webhook.set_ingest_use_case(ingest_service)
    yield
    await kafka_publisher.stop()


app = FastAPI(
    title="mimir-ingest",
    description="git push webhook 수신 → diff 파싱 → NoteChangedEvent 발행",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router, prefix="/webhooks")


@app.get("/health", tags=["health"])
async def health() -> dict:
    """헬스체크 엔드포인트."""
    return {"status": "ok"}
