"""HybridSearcher 구현체 — OpenSearch 하이브리드 검색 (벡터 + BM25)."""
import os

from opensearchpy import AsyncOpenSearch

from mimir_api.domain.models import NoteDetail, NoteRef
from mimir_api.ports.outbound import HybridSearcher

INDEX_NAME = "mimir-notes"


class OpenSearchAdapter(HybridSearcher):
    """OpenSearch 쿼리로 노트를 검색한다."""

    def __init__(self, host: str, port: int) -> None:
        self._client = AsyncOpenSearch(hosts=[{"host": host, "port": port}])

    async def search(self, query: str, top_k: int = 5) -> list[NoteRef]:
        """BM25 키워드 검색으로 노트 청크를 조회한다.

        TODO: knn 벡터 검색과 결합한 하이브리드 쿼리로 교체.
        """
        response = await self._client.search(
            index=INDEX_NAME,
            body={
                "size": top_k,
                "query": {"match": {"content": query}},
                "_source": ["noteId", "content"],
            },
        )

        results: list[NoteRef] = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append(NoteRef(
                note_id=source.get("noteId", ""),
                file_path="",
                score=hit["_score"],
                snippet=source.get("content", "")[:200],
            ))
        return results

    async def get_note(self, note_id: str) -> NoteDetail | None:
        """note_id 기준으로 첫 번째 청크의 내용을 반환한다."""
        response = await self._client.search(
            index=INDEX_NAME,
            body={
                "size": 1,
                "query": {"term": {"noteId.keyword": note_id}},
                "_source": ["noteId", "content"],
            },
        )
        hits = response["hits"]["hits"]
        if not hits:
            return None

        source = hits[0]["_source"]
        return NoteDetail(
            note_id=source.get("noteId", note_id),
            file_path="",
            content=source.get("content", ""),
            frontmatter={},
        )
