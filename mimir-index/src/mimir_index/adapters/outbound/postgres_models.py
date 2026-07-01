"""SQLAlchemy ORM 모델 — PostgreSQL 테이블 정의.

Python 속성명과 DB 컬럼명 모두 snake_case (PEP 8 + PostgreSQL 관례).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class NoteModel(Base):
    """notes 테이블 — 노트 메타데이터."""

    __tablename__ = "notes"

    note_id = Column(String, primary_key=True)
    file_path = Column(String, nullable=False)
    tags = Column(ARRAY(String), nullable=False, default=list)
    project = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="")
    commit_hash = Column(String, nullable=False)
    indexed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChunkModel(Base):
    """chunks 테이블 — 임베딩 청크 메타데이터.

    실제 벡터는 OpenSearch에 저장하고 여기서는 매핑 정보만 관리한다.
    """

    __tablename__ = "chunks"

    chunk_id = Column(String, primary_key=True)
    note_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
