"""mimir-api FastAPI 애플리케이션 엔트리포인트."""
import os

from fastapi import FastAPI

from mimir_api.adapters.inbound import mcp_server, router as router_module
from mimir_api.adapters.inbound.router import router as api_router
from mimir_api.adapters.outbound.llm_client import AnthropicSynthesizer
from mimir_api.adapters.outbound.opensearch_adapter import OpenSearchAdapter
from mimir_api.services.query_service import QueryService

opensearch_adapter = OpenSearchAdapter(
    host=os.getenv("OPENSEARCH_HOST", "opensearch"),
    port=int(os.getenv("OPENSEARCH_PORT", "9200")),
)
synthesizer = AnthropicSynthesizer()
query_service = QueryService(searcher=opensearch_adapter, synthesizer=synthesizer)

router_module.set_query_use_case(query_service)
mcp_server.set_query_use_case(query_service)

app = FastAPI(
    title="mimir-api",
    description="vault 하이브리드 검색 + LLM 합성 답변 API (MCP 서버 겸용)",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> dict:
    """헬스체크 엔드포인트."""
    return {"status": "ok"}
