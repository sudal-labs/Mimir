"""mimir-link 엔트리포인트."""
import asyncio
import logging

from mimir_link.adapters.inbound.kafka_consumer import KafkaLinkConsumer
from mimir_link.adapters.outbound.llm_client import AnthropicLinkClient
from mimir_link.adapters.outbound.vault_writer import GitVaultWriter
from mimir_link.services.link_service import LinkService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def build_similarity_searcher():
    """SimilaritySearcher 플레이스홀더."""
    from mimir_link.ports.outbound import SimilaritySearcher

    class PlaceholderSimilaritySearcher(SimilaritySearcher):
        async def find_similar_notes(self, note_id: str, content: str, top_k: int = 5) -> list[dict]:
            raise NotImplementedError("SimilaritySearcher 구현이 필요합니다.")

    return PlaceholderSimilaritySearcher()


async def main() -> None:
    link_service = LinkService(
        similarity_searcher=build_similarity_searcher(),
        llm_link_client=AnthropicLinkClient(),
        vault_writer=GitVaultWriter(),
    )
    consumer = KafkaLinkConsumer(link_use_case=link_service)
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
