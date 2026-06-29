---
name: mcp-python-sdk
description: vault-api를 MCP 서버로 감싸 Claude Code 등에서 도구 호출로 연동할 때 사용. FastMCP 툴 정의 패턴과 claude mcp add 등록 방법.
---

# SKILL: mcp (Python SDK)

해당 모듈: `vault-api` 위에 얇게 씌우는 MCP 서버 (별도 진입점, 예: `mimir_mcp_server`)

## 설치
```
pip install mcp
```

## 사용 패턴
```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("mimir")

@server.tool()
def search_notes(query: str, top_k: int = 5) -> list[dict]:
    """이 프로젝트나 다른 프로젝트의 과거 노트에서 query와 관련된 내용을 찾을 때 사용.
    하이브리드(키워드+벡터) 검색 결과를 노트 제목/경로/요약과 함께 반환한다."""
    return vault_api_client.search(query, top_k)

@server.tool()
def get_note(note_id: str) -> dict:
    """특정 노트의 전체 내용을 가져온다."""
    return vault_api_client.get(note_id)

@server.tool()
def suggest_links(note_id: str) -> list[dict]:
    """주어진 노트와 연결될 가능성이 높은 다른 노트들을 제안한다."""
    return vault_api_client.suggest_links(note_id)

if __name__ == "__main__":
    server.run()
```

## Claude Code 등록
```
claude mcp add --transport stdio mimir --scope user -- python -m mimir_mcp_server
```
`--scope user`로 등록하면 어떤 리포에서 Claude Code를 켜도 mimir 툴에 접근 가능.

확인:
```
claude mcp list
```
세션 안에서 `/mcp`로 연결된 서버와 등록된 툴 목록 확인 가능.

## 주의
- 툴 `description`(docstring)이 Claude가 언제 이 툴을 호출할지 판단하는 유일한 단서. 모호하게
  쓰면 호출이 안 되거나 엉뚱하게 호출됨 — "이 프로젝트의 과거 결정이나 다른 프로젝트와의 연관성을
  찾을 때 사용" 식으로 사용 시점을 구체적으로 명시할 것
- vault-api가 죽어있으면 MCP 서버도 같이 죽으므로, 헬스체크 실패 시 명확한 에러 메시지를
  반환하도록 처리 (Claude Code 쪽에서 "서버 연결 실패" 원인 파악이 쉬워짐)