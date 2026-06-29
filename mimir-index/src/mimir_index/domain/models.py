"""mimir-index 도메인 모델"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NoteChunk:
    """
    임베딩 단위로 분할된 노트 청크

    OpenSearch 벡터 인덱스의 한 문서에 대응한다.
    """

    chunk_id: str
    """'{note_id}_{chunk_index}' 형태의 고유 식별자"""

    note_id: str
    """원본 노트 식별자"""

    content: str
    """청크 텍스트 내용"""

    chunk_index: int
    """노트 내 청크 순번 (0-based)"""

    embedding: list[float] = field(default_factory=list)
    """sentence-transformers 생성 임베딩 벡터, 인덱싱 전까지는 빈 리스트"""


@dataclass
class NoteMetadata:
    """
    PostgreSQL에 저장되는 노트 메타데이터

    notes 테이블의 도메인 표현
    """

    note_id: str
    file_path: str
    tags: list[str]
    project: str
    status: str
    commit_hash: str
    indexed_at: datetime
