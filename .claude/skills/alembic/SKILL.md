---
name: alembic
description: PostgreSQL 스키마 마이그레이션(노트 메타데이터, 링크 그래프 테이블)을 추가하거나 변경할 때 사용. revision/upgrade 패턴과 autogenerate 검토 주의사항.
---

# SKILL: Alembic

해당 모듈: `vault-index`, `vault-link`, `vault-api` (PostgreSQL 사용하는 모듈 전체)

## 설치
```
pip install alembic
```

## 초기 설정
```
alembic init migrations
```
`alembic.ini`의 `sqlalchemy.url`은 하드코딩하지 말고 환경변수에서 읽도록 `env.py`에서 처리.

## 사용 패턴
모델(SQLAlchemy) 변경 시:
```
alembic revision --autogenerate -m "노트 메타데이터 테이블 추가"
```
생성된 마이그레이션 파일을 **반드시 직접 검토**한 뒤:
```
alembic upgrade head
```

## 대상 테이블 (예상)
- `notes` (메타데이터: path, 태그, 프로젝트, 날짜, 상태, 임베딩 인덱스 참조)
- `note_links` (link graph: note_id_a, note_id_b, relation_type, confidence, created_at)

## 주의
- `--autogenerate`는 인덱스나 제약조건을 완벽히 잡아내지 못하는 경우가 있음. 생성된 파일은
  항상 리뷰하고 누락된 인덱스(예: 벡터 검색과 연계되는 note_id 인덱스)는 직접 추가
- 스키마가 안정화된 이후엔 마이그레이션 빈도가 자연히 줄어듦 — 그래도 제거하지 말고 유지
  (DESIGN_NOTES.md 참고)