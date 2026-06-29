---
name: sentence-transformers
description: vault-index 모듈에서 노트 청크의 로컬 임베딩을 생성할 때 사용. 다국어 모델 선택, 배치 인코딩 패턴, OpenSearch 벡터 차원 설정 가이드.
---

# SKILL: sentence-transformers (로컬 임베딩)

해당 모듈: `vault-index`

## 설치
```
pip install sentence-transformers --break-system-packages
```

## 모델 선택
노트 대부분이 한국어이므로 **다국어 모델을 반드시 사용**할 것. 영어 전용 모델(예: `all-MiniLM-L6-v2`)은
한국어 임베딩 품질이 떨어짐.

추천: `paraphrase-multilingual-MiniLM-L12-v2` (384차원, 가벼움 — ARM CPU 환경에 적합)

## 사용 패턴
- 프로세스 시작 시 모델을 한 번 로드해서 재사용 (매 요청마다 로드하면 느림 — FastAPI에서는 앱
  startup 이벤트에서 singleton으로 로드)
- 배치 인코딩: 청크 리스트를 한 번에 `model.encode(chunks, batch_size=8)` 호출 (GPU 없는
  환경이라 batch_size를 크게 잡으면 메모리 압박, 8~16 정도로 시작)
- OpenSearch 인덱스의 벡터 필드 dims는 모델 출력 차원과 정확히 일치시킬 것 (MiniLM 계열 = 384)

## 주의
- CPU 추론 속도가 느리므로 실시간 응답 경로(vault-api 질문 응답)보다는 배치 인덱싱 경로
  (vault-index)에서만 사용. 질문 임베딩은 동일 모델로 빠르게 1건만 인코딩하면 되므로 실시간
  경로에서도 괜찮음 — 문제는 노트 전체를 재인덱싱하는 배치 쪽
- 노트 수가 늘어 배치 시간이 부담되면 DESIGN_NOTES.md의 "설계가 깨지는 시점" 참고