"""mimir-api REST 라우터.

엔드포인트:
    POST /api/v1/notes/search  — 질문 검색 + LLM 합성 답변
    GET  /api/v1/notes/{note_id} — 단일 노트 조회
    GET  /api/v1/notes/{note_id}/links — 연관 노트 목록
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from mimir_api.ports.inbound import QueryUseCase

router = APIRouter(tags=["notes"])

_query_use_case: QueryUseCase | None = None


def set_query_use_case(use_case: QueryUseCase) -> None:
    global _query_use_case
    _query_use_case = use_case


class SearchBody(BaseModel):
    """POST /notes/search 요청 본문. JSON camelCase → Python snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query: str
    top_k: int = 5


@router.post("/notes/search")
async def search_notes(body: SearchBody) -> dict:
    """질문에 대한 하이브리드 검색 결과와 LLM 합성 답변을 반환한다."""
    if _query_use_case is None:
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다.")

    response = await _query_use_case.search_notes(query=body.query, top_k=body.top_k)
    return {
        "answer": response.answer,
        "sourceNotes": [
            {"noteId": ref.note_id, "filePath": ref.file_path, "score": ref.score, "snippet": ref.snippet}
            for ref in response.source_notes
        ],
    }


@router.get("/notes/{note_id}")
async def get_note(note_id: str) -> dict:
    """단일 노트를 note_id로 조회한다."""
    if _query_use_case is None:
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다.")

    note = await _query_use_case.get_note(note_id=note_id)
    if note is None:
        raise HTTPException(status_code=404, detail=f"노트를 찾을 수 없습니다: {note_id}")

    return {
        "noteId": note.note_id,
        "filePath": note.file_path,
        "content": note.content,
        "frontmatter": note.frontmatter,
        "relatedNoteIds": note.related_note_ids,
    }


@router.get("/notes/{note_id}/links")
async def suggest_links(note_id: str) -> dict:
    """note_id와 연관된 노트 ID 목록을 반환한다."""
    if _query_use_case is None:
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다.")

    related_note_ids = await _query_use_case.suggest_links(note_id=note_id)
    return {"noteId": note_id, "relatedNoteIds": related_note_ids}
