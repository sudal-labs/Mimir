---
name: python-frontmatter
description: 마크다운 노트의 YAML frontmatter를 파싱하거나 작성할 때 사용 (vault-ingest, vault-link). 필수 필드 검증, 재직렬화 시 git diff 주의사항.
---

# SKILL: python-frontmatter

해당 모듈: `vault-ingest`, `vault-link`

## 설치
```
pip install python-frontmatter
```

## 사용 패턴

읽기:
```python
import frontmatter
post = frontmatter.load(file_path)
post.metadata   # dict: 태그, 프로젝트, 날짜, 상태 등
post.content    # 마크다운 본문 (frontmatter 제외)
```

쓰기 (재직렬화):
```python
frontmatter.dumps(post)
```

## 필수 frontmatter 필드 (OVERVIEW.md 4번 컨벤션)
- 태그
- 프로젝트
- 날짜
- 상태

ingest 단계에서 pydantic 모델로 감싸서 필수 필드 누락을 검증할 것.

## 주의
- `frontmatter.dumps()`로 재직렬화하면 dict 순서나 YAML 포맷이 원본과 달라져 git diff가
  지저분해질 수 있음. backlink 추가처럼 본문만 바뀌는 경우엔 frontmatter는 그대로 두고 본문
  텍스트만 직접 append하는 방식을 권장 (전체 재직렬화 피하기)
- frontmatter가 단순 key-value를 넘어서는 관계형 데이터(노트 간 링크 그래프 등)를 담아야 하는
  상황이 오면 DESIGN_NOTES.md "설계가 깨지는 시점" 참고 — PostgreSQL 메타데이터 테이블로 이전