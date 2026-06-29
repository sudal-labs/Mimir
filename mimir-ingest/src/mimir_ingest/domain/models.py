"""mimir-ingest 도메인 모델"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class FrontmatterData:
    """마크다운 노트 YAML frontmatter의 필수 필드 파싱 결과

    OVERVIEW.md에서 정의한 필수 필드: tags, project, date, status
    그 외 필드는 extra에 수집한다.
    """

    tags: list[str] = field(default_factory=list)
    project: str = ""
    date: str = ""
    status: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class NoteChangedEvent:
    """git commit 으로 변경된 마크다운 노트 하나의 도메인 이벤트

    vault-ingest가 Kafka 토픽 'mimir.note.changed'에 발행하는 이벤트
    vault-index, vault-link가 이 이벤트를 소비한다.
    """

    note_id: str
    """vault 내 파일 경로 기반 슬러그 (예: 'projects_mimir_design_md')"""

    file_path: str
    """vault 저장소 루트 기준 상대 경로 (예: 'projects/mimir/design.md')"""

    change_type: str
    """변경 유형: 'added' | 'modified' | 'deleted'"""

    content: str
    """변경 후 파일 전체 내용. change_type이 'deleted' 이면 빈 문자열"""

    frontmatter: FrontmatterData
    """파싱된 YAML frontmatter"""

    commit_hash: str
    """이벤트가 발생한 git 커밋 SHA"""

    occurred_at: datetime
    """커밋 타임스탬프 (Asia/Seoul 기준)"""
