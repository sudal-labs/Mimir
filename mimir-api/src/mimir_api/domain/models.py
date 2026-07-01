"""mimir-api 도메인 모델."""
from dataclasses import dataclass, field


@dataclass
class NoteRef:
    """검색 결과에서 참조된 노트."""

    note_id: str
    file_path: str
    score: float
    snippet: str


@dataclass
class SearchRequest:
    """vault 검색 요청."""

    query: str
    top_k: int = 5
    use_hybrid: bool = True


@dataclass
class SearchResponse:
    """vault 검색 응답 — LLM 합성 답변 + 근거 노트 링크."""

    answer: str
    source_notes: list[NoteRef] = field(default_factory=list)


@dataclass
class NoteDetail:
    """단일 노트 조회 결과."""

    note_id: str
    file_path: str
    content: str
    frontmatter: dict
    related_note_ids: list[str] = field(default_factory=list)
