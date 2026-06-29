# Mimir

여러 프로젝트의 문서와 학습 기록을 git 기반 vault에 누적시키고, 자동으로 인덱싱·연결해서 LLM이
조회할 수 있는 "내 모델"로 만드는 개인용 지식 관리 파이프라인입니다.

노트를 쓰고 git push만 하면 인덱싱과 연결 제안까지 백그라운드에서 자동으로 처리되고,
질문할 때는 vault-api(또는 MCP를 통해 Claude Code)로 바로 물어볼 수 있습니다.

## 아키텍처

5개 모듈이 hexagonal architecture로 독립 구성되어 있습니다. 의존성이 적은 순서대로 구현합니다.

| 모듈 | 역할 |
|---|---|
| `mimir-ingest` | git webhook 수신, diff 파싱, frontmatter 추출 → 이벤트 발행 |
| `mimir-index` | 노트 청킹·임베딩 → OpenSearch(하이브리드 검색)·PostgreSQL(메타데이터) 적재 |
| `mimir-link` | 신규/수정 노트에 대해 LLM이 연결점을 제안 → backlink commit |
| `mimir-api` | 질문 → 하이브리드 검색 → LLM 합성 → 근거 노트 링크 포함 답변 |
| `mimir-scheduler` | Airflow 배치: 야간 전체 재인덱싱, 주간 학습 다이제스트 |
| `mimir-mcp-server` | `mimir-api`를 MCP 서버로 감싸 Claude Code 등에서 도구 호출로 접근 |

## 데이터 흐름

**쓸 때 (자동)**
노트 작성 → git push → webhook 수신(ingest) → 이벤트 발행(Kafka) → 인덱싱(index) → 연결 제안(link, Claude/Grok) → backlink commit

**물어볼 때 (직접)**
질문 입력 → 요청 처리(api) → 하이브리드 검색(OpenSearch) → LLM 합성(Claude/Grok) → 근거 링크 포함 답변

**주기적으로 (배치)**
Airflow가 야간 전체 재인덱싱, 주간 학습 다이제스트를 자동 생성

## 기술 스택

| 영역 | 기술 |
|---|---|
| 언어/프레임워크 | Python 3.12+, FastAPI |
| 데이터베이스 | PostgreSQL(메타데이터, 링크 그래프), MongoDB(비정형 로그) |
| 검색/벡터 | OpenSearch (키워드+벡터 하이브리드) |
| 메시징 | Kafka (KRaft) |
| 배치/스케줄링 | Airflow |
| 관측성 | Grafana, Loki |
| LLM 프로바이더 | Claude, Grok |
| 임베딩 | sentence-transformers (로컬, 다국어 모델) |
| 컨테이너 | Podman / podman-compose |
| CI | GitHub Actions |
| 아키텍처 | Hexagonal, 모듈형 |

세부 트레이드오프와 선택 이유는 [`DESIGN_NOTES.md`](./DESIGN_NOTES.md), 스택 결정 절차는
[`STACK.md`](./STACK.md)를 참고하세요.

## 프로젝트 구조

```
mimir/
├── CLAUDE.md            # Claude 세션 진입점
├── OVERVIEW.md          # 프로젝트 개요, 요구사항, 제한사항
├── STACK.md             # 기술 스택 및 확장 스택 의사결정 기록
├── DESIGN_NOTES.md       # 기능별 트레이드오프 / 설계가 깨지는 시점 / 선택 이유
├── .claude/
│   └── skills/           # 확정된 확장 스택의 상세 가이드 (필요할 때만 로드)
├── mimir-ingest/
├── mimir-index/
├── mimir-link/
├── mimir-api/
├── mimir-scheduler/
├── mimir-mcp-server/
├── podman-compose.yml
└── README.md
```

## 시작하기

> 현재 구현 초기 단계입니다 — `mimir-ingest`부터 순서대로 작업 중입니다. 아래는 예정된 구조 기준 안내입니다.

```bash
git clone <repo-url>
cd mimir
cp .env.example .env   # PostgreSQL/MongoDB/Kafka/OpenSearch 접속 정보, Claude/Grok API 키 설정
podman-compose up -d
```

## Claude Code 연동

`mimir-mcp-server`가 준비되면 아래처럼 등록해서 어떤 리포에서도 vault를 조회할 수 있습니다.

```bash
claude mcp add --transport stdio mimir --scope user -- python -m mimir_mcp_server
```

## 로드맵

- [ ] mimir-ingest
- [ ] mimir-index
- [ ] mimir-link
- [ ] mimir-api
- [ ] mimir-scheduler
- [ ] mimir-mcp-server

## 문서

- [`OVERVIEW.md`](./OVERVIEW.md) — 프로젝트 개요, 요구사항, 제한사항
- [`STACK.md`](./STACK.md) — 기술 스택, 확장 스택 의사결정 사이클
- [`DESIGN_NOTES.md`](./DESIGN_NOTES.md) — 기능별 설계 근거