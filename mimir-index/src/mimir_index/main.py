"""mimir-index 엔트리포인트 — Kafka 소비자를 조립하고 시작한다."""
import asyncio
import logging
import os

from mimir_index.adapters.inbound.kafka_consumer import KafkaIndexConsumer
from mimir_index.adapters.outbound.opensearch_adapter import OpenSearchAdapter
from mimir_index.adapters.outbound.postgres_adapter import PostgresAdapter
from mimir_index.services.index_service import IndexService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def build_embedding_generator():
    """sentence-transformers EmbeddingGenerator 플레이스홀더."""
    from mimir_index.ports.outbound import EmbeddingGenerator

    class PlaceholderEmbeddingGenerator(EmbeddingGenerator):
        def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
            raise NotImplementedError("EmbeddingGenerator 구현이 필요합니다.")

    return PlaceholderEmbeddingGenerator()


async def main() -> None:
    opensearch_adapter = OpenSearchAdapter(
        host=os.getenv("OPENSEARCH_HOST", "opensearch"),
        port=int(os.getenv("OPENSEARCH_PORT", "9200")),
    )
    postgres_adapter = PostgresAdapter()
    embedding_generator = build_embedding_generator()

    index_service = IndexService(
        embedding_generator=embedding_generator,
        vector_store=opensearch_adapter,
        metadata_store=postgres_adapter,
    )

    consumer = KafkaIndexConsumer(index_use_case=index_service)
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
