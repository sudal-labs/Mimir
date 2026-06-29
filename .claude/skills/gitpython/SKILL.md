---
name: gitpython
description: vault-ingest의 git diff 감지나 vault-link의 backlink commit/push를 구현할 때 사용. GitPython 사용 패턴과 동시성 주의사항.
---

# SKILL: GitPython

해당 모듈: `vault-ingest`, `vault-link`

## 설치
```
pip install GitPython
```

## 사용 패턴

### diff 감지 (vault-ingest)
```python
from git import Repo
repo = Repo(vault_path)
changed_files = repo.git.diff(prev_commit, new_commit, name_only=True).splitlines()
```

특정 커밋 시점의 파일 내용 조회:
```python
content = repo.git.show(f"{commit_sha}:{file_path}")
```

### backlink commit (vault-link)
```python
# 1. 파일 수정 (frontmatter/본문에 backlink 섹션 추가)
# 2. 스테이징 + 커밋 + push
repo.index.add([file_path])
repo.index.commit(f"mimir: add backlinks to {file_path}")
repo.remote(name="origin").push()
```

## 주의
- webhook은 비동기로 들어오므로 동시에 여러 push가 겹칠 수 있음. Kafka consumer를 단일
  파티션(또는 키 기반 파티셔닝)으로 처리하면 같은 파일에 대한 처리가 자연스럽게 직렬화됨
- backlink commit이 사용자가 직접 작성 중인 노트와 충돌할 수 있으니, push 전에 최신 origin을
  pull/rebase 하는 로직 필요
- vault가 커지면 풀 diff 계산이 느려짐 — DESIGN_NOTES.md "설계가 깨지는 시점" 참고