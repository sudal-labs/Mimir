# OVERVIEW.md — 프로젝트 개요
> 새 프로젝트를 시작할 때 이 파일과 STACK.md의 "프로젝트 스택" 영역만 채우면 됩니다.
> "확장 스택"은 사용자가 미리 정하는 게 아니라, 아래 요구사항/제한사항을 Claude가 분석해서
> STACK.md에 직접 채웁니다. 컨벤션/워크플로우는 4~5번 섹션에 예외가 있을 때만 적으면 됩니다.
>
> 2번(핵심 요구사항)·3번(제한사항)의 각 항목에는 WORKFLOW.md "의사결정 사이클" 상태 표기를
> 붙입니다. 처음 정의된 범위는 `🟢 확정`으로 두고, 진행 중 새로 떠오르는 확장/변경 제안은
> `🟡 제안`으로 추가한 뒤 같은 사이클(제안 → 검수 → 피드백 → 확정)을 거쳐 상태를 바꿉니다.
> 검토 후 채택하지 않기로 했다면 지우지 말고 `🔴 기각`으로 남깁니다.

## 1. 프로젝트 요약
- 한 줄 설명: 여러 프로젝트의 문서·학습 기록을 git 기반 vault에 누적시키고, 자동으로 인덱싱·연결하여 LLM이 조회 가능한 "내 모델"로 만드는 개인용 지식 관리(PKM) 파이프라인 (프로젝트명: Mimir)
- 목적/배경: 프로젝트별로 흩어져 있는 문서/학습 노트를 한 곳에 모으고, 새 노트가 들어올 때 기존 노트와 자동으로 연결되게 해서 Claude Code 등에서 질문할 때 개인 맥락을 즉시 활용. git commit 이력 자체가 학습 흐름의 보존 기록이 되는 것도 목적 중 하나.
- 핵심 도메인 흐름: 노트 작성(git push) → ingest(webhook 수신, diff 파싱) → 이벤트 발행(Kafka) → 인덱싱(청킹·임베딩 → OpenSearch+PostgreSQL) → 연결 제안(LLM 호출 → backlink 커밋) → 조회(vault-api: 하이브리드 검색 → LLM 합성 → 근거 링크 포함 답변) → 정기 배치(Airflow: 재인덱싱, 주간 다이제스트)

> 기술 스택(언어/프레임워크/DB/확장 스택/외부 데이터 소스)은 STACK.md에서 관리합니다.

## 2. 핵심 요구사항

### 기능 요구사항
- 🟢 git 기반 vault(마크다운+frontmatter)의 변경 감지(vault-ingest) → 파싱 → 이벤트 발행
- 🟢 노트 청킹·임베딩 후 OpenSearch(벡터+키워드 하이브리드 인덱스)·PostgreSQL(메타데이터)에 적재 (vault-index)
- 🟢 새/수정 노트에 대해 기존 노트와의 연결점을 LLM(Claude/Grok)이 제안하고, 결과를 backlink로 노트 파일에 다시 commit (vault-link)
- 🟢 외부에서 vault를 검색/조회하는 API 제공: 질문 → 하이브리드 검색 → LLM 합성 → 근거 노트 링크 포함 답변 (vault-api)
- 🟢 vault-api를 MCP 서버로 감싸 Claude Code 등 외부 클라이언트가 도구 호출(`search_notes`, `get_note`, `suggest_links`) 형태로 vault에 접근 가능하게 함
- 🟡 정기 배치(vault-scheduler): 야간 전체 재인덱싱, 주간 학습 다이제스트 생성 — 구체적 Airflow DAG/스케줄은 모듈 구현 시점에 확정

### 비기능 요구사항
- 🟢 5개 모듈(vault-ingest / vault-index / vault-link / vault-api / vault-scheduler)을 hexagonal architecture로 독립 구성, 모듈 간 결합 최소화. 기존 LLM 멀티 라우팅 프로젝트(Kotlin/Spring)와는 완전히 별도 — 코드/인프라 재사용 없음
- 🟢 1인 운영 기준 리소스 효율: 풀스택(OpenSearch+Kafka+MongoDB+PostgreSQL+Airflow+Grafana/Loki) 상시 가동 시 RAM 16GB 이상을 전제로 설계. Kafka 토픽 retention은 짧게(이벤트 버스 용도, 영구 저장소 아님), Loki 로그도 retention 정책 적용해 디스크 사용량 관리
- 🟡 배치성 작업(야간 재인덱싱 등)은 상시 가동 인스턴스 대신 시간당 과금 인스턴스로 분리 실행 가능하도록 설계 — 실제 분리 여부는 운영 단계에서 결정
- 🟡 ARM(Hetzner CAX 계열) 배포 호환성: Python/FastAPI 자체는 문제 없을 것으로 예상하나, 임베딩 모델 등 의존성의 ARM 호환은 구현 단계에서 확인 필요

## 3. 제한사항
- 🟢 이전 멀티 LLM 라우팅 프로젝트(Kotlin/Spring, hexagonal, OpenSearch/Kafka/Podman 동일 스택 사용)와는 완전히 독립된 신규 프로젝트로 진행 — 의존성 없음
- 🟢 LLM 프로바이더는 Claude, Grok만 사용 (Gemini/GPT/Ollama 미사용)
- 🟢 개발 환경 고정: Python 3.12+ / FastAPI
- 🟢 1인 개인 운영 목적 — 멀티테넌시/권한 관리 등 다중 사용자 시나리오는 고려하지 않음
- 🟡 임베딩 모델은 자체 호스팅(로컬) 우선 검토 — GPU 없는 ARM 환경 기준 처리 속도 제약이 있어, 실시간 임베딩보다는 배치 인덱싱 위주로 설계

## 4. 프로젝트 특이 컨벤션
- 모듈명 prefix: `mimir-` (예: `mimir-ingest`, `mimir-index`, `mimir-link`, `mimir-api`, `mimir-scheduler`)
- 노트 frontmatter 필수 필드: 태그, 프로젝트, 날짜, 상태 (추가 필드는 구현 중 확정되면 갱신)

## 5. 프로젝트 특이 워크플로우
- 응답 언어: 한국어 (기본값 유지)
- 구현 순서: vault-ingest → vault-index → vault-link → vault-api → vault-scheduler (의존성 적은 모듈부터)

## 6. 작성해야 할 문서
| 문서 | 상태 | 경로 |
|---|---|---|
| DESIGN_NOTES.md (기능별 트레이드오프 / 설계가 깨지는 시점 / 선택 이유) | ☐ 없음 / ☑ 있음 | `DESIGN_NOTES.md` |

> Claude 지침: "없음"으로 체크된 문서와 직접 관련된 작업을 요청받으면,
> 코드를 바로 작성하지 말고 해당 문서의 초안 작성을 먼저 제안할 것.
> STACK.md의 확장 스택 항목이 🟢 확정될 때마다, 해당 결정의 트레이드오프·설계가 깨지는 시점·
> 선택 이유를 DESIGN_NOTES.md에 같은 형식으로 이어서 기록할 것.

## 7. 원본 참고 자료
해당 없음 — 개인 프로젝트로, 별도 과제 원본/외부 입력 파일 없음.