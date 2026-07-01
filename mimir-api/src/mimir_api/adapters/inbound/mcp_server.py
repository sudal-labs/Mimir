"""MCP 서버 — vault-api를 Claude Code 등에서 도구 호출로 접근 가능하게 감싼다.

등록 방법: claude mcp add mimir-vault -- python -m mimir_api.adapters.inbound.mcp_server
"""
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mimir_api.ports.inbound import QueryUseCase

MCP_SERVER_NAME = "mimir-vault"

server = Server(MCP_SERVER_NAME)

_query_use_case: QueryUseCase | None = None


def set_query_use_case(use_case: QueryUseCase) -> None:
    """MCP 서버에 QueryUseCase를 주입한다."""
    global _query_use_case
    _query_use_case = use_case


@server.list_tools()
async def list_tools() -> list[Tool]:
    """MCP 클라이언트에 노출할 도구 목록을 반환한다."""
    return [
        Tool(
            name="search_notes",
            description="개인 vault를 하이브리드 검색해 관련 노트를 찾고 LLM으로 답변을 합성한다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 질문"},
                    "topK": {"type": "integer", "description": "반환할 최대 노트 수", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_note",
            description="note_id로 vault의 단일 노트 전체 내용을 가져온다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "noteId": {"type": "string", "description": "노트 슬러그 ID"},
                },
                "required": ["noteId"],
            },
        ),
        Tool(
            name="suggest_links",
            description="note_id와 연관된 다른 노트 ID 목록을 반환한다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "noteId": {"type": "string", "description": "대상 노트 ID"},
                },
                "required": ["noteId"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 호출을 QueryUseCase에 위임하고 결과를 TextContent로 반환한다."""
    if _query_use_case is None:
        return [TextContent(type="text", text="서비스가 초기화되지 않았습니다.")]

    if name == "search_notes":
        query = arguments["query"]
        top_k = int(arguments.get("topK", 5))
        response = await _query_use_case.search_notes(query=query, top_k=top_k)
        lines = [f"**답변**: {response.answer}", ""]
        for ref in response.source_notes:
            lines.append(f"- [{ref.file_path}] score={ref.score:.2f}: {ref.snippet}")
        return [TextContent(type="text", text="\n".join(lines))]

    if name == "get_note":
        note_id = arguments["noteId"]
        note = await _query_use_case.get_note(note_id=note_id)
        if note is None:
            return [TextContent(type="text", text=f"노트를 찾을 수 없습니다: {note_id}")]
        return [TextContent(type="text", text=note.content)]

    if name == "suggest_links":
        note_id = arguments["noteId"]
        related_note_ids = await _query_use_case.suggest_links(note_id=note_id)
        return [TextContent(type="text", text="\n".join(related_note_ids) or "연관 노트가 없습니다.")]

    return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]


async def run_mcp_server() -> None:
    """stdio 기반 MCP 서버를 실행한다."""
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
