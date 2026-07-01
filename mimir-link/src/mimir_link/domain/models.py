"""mimir-link 도메인 모델."""
from dataclasses import dataclass, field


@dataclass
class LinkSuggestion:
    """LLM이 제안한 노트 간 연결 하나."""

    source_note_id: str
    target_note_id: str
    target_file_path: str
    reason: str
    """LLM이 제시한 연결 이유 (한 문장)."""
    confidence: float
    """0.0 ~ 1.0. 임계값(기본 0.7) 미만이면 커밋하지 않는다."""


@dataclass
class BacklinkEntry:
    """vault 노트 파일의 frontmatter에 삽입될 관련 노트 목록."""

    note_id: str
    file_path: str
    related_note_ids: list[str] = field(default_factory=list)
