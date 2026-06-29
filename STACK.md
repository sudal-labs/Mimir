# STACK.md — 기술 스택

## 프로젝트 스택 (이 프로젝트에서 실제로 쓰는 값 — 새 프로젝트마다 갱신)

### 공통 스택
- Python 버전: 3.14
- 웹 프레임워크: FastAPI
- ORM / DB 드라이버: SQLAlchemy (PostgreSQL), Motor 또는 PyMongo (MongoDB)
- 데이터베이스: PostgreSQL(메타데이터, 링크 그래프) + MongoDB(비정형 로그, LLM 응답 원본)
- 검색/벡터 저장소: OpenSearch (k-NN 벡터 + 키워드 하이브리드)
- 메시징: Kafka — KRaft 모드(Zookeeper 미사용), 이벤트 버스 용도이므로 토픽 retention 짧게(1~3일) 설정
- 배치/스케줄링: Airflow (LocalExecutor) — 야간 재인덱싱, 주간 학습 다이제스트
- 관측성: Grafana + Loki
- LLM 프로바이더: Claude, Grok (API 직접 호출)
- 패키지 관리: pip (requirements.txt)
- 컨테이너/배포: Podman / podman-compose (모든 컴포넌트 컨테이너화), GitHub Actions(CI, 옵션으로 Quartz 퍼블리싱)
- 아키텍처: Hexagonal, 모듈별 독립 패키지 — `mimir-ingest` / `mimir-index` / `mimir-link` / `mimir-api` / `mimir-scheduler`

### 전체 컨테이너화
모든 프로세스는 컨테이너화 되어 make 명령어로 동작합니다.

Makefile 예시
```makefile

COMPOSE = podman compose -f podman/compose.yml

.PHONY: setup run down logs status rebuild test

# 이미지 빌드
setup:
	@podman info >/dev/null 2>&1 || { \
		echo "Podman Machine이 실행되고 있지 않습니다."; \
		echo "Podman Machine을 실행한 뒤 다시 시도해주세요."; \
		exit 1; \
	}
	$(COMPOSE) build

# 전체 서비스 실행
run:
	@podman info >/dev/null 2>&1 || { \
		echo "Podman Machine이 실행되고 있지 않습니다."; \
		echo "Podman Machine을 실행한 뒤 다시 시도해주세요."; \
		exit 1; \
	}
	$(COMPOSE) up -d
	@echo ""
	@echo "API        → http://localhost:8000/docs"
	@echo "PostgreSQL → localhost:5432  (postgres / postgres)"
	@echo "MinIO 콘솔  → http://localhost:9001  (minioadmin / minioadmin)"
	@echo "Kafka      → localhost:9092"

# 컨테이너, 볼륨, 로컬 빌드 이미지 정리
down:
	@read -p "볼륨과 로컬 이미지를 모두 삭제합니다. 계속할까요? (y/N) " confirm && \
	[ "$$confirm" = "y" ] && $(COMPOSE) down -v --rmi local || echo "취소됐습니다."

# 로그 확인 (ex: make logs api)
logs:
	$(COMPOSE) logs -f $(filter-out $@,$(MAKECMDGOALS))

# 실행 상태 확인
status:
	$(COMPOSE) ps

# 코드 변경 후 특정 서비스만 재빌드 (ex: make rebuild api worker)
rebuild:
	$(COMPOSE) up -d --build $(filter-out $@,$(MAKECMDGOALS))

# 단위 테스트 실행 (로컬 venv 필요: pip install -r requirements.txt)
test:
	.venv/bin/pytest tests/ -v

# 오류 방지
%:
	@:
```

### 테스트/품질 도구
- 테스트 프레임워크: pytest
- 린트: ruff
- 타입 체크: mypy

### 확장 스택 (Claude가 분석해서 직접 채우는 영역)
공통 스택만으로 OVERVIEW.md의 요구사항/제한사항을 만족하기 어려운 지점이 있는지 먼저 점검하고,
필요할 때만 아래 절차로 판단해서 표를 채웁니다. 상태 표기는 WORKFLOW.md "의사결정 사이클"을
그대로 따릅니다(🟡 제안 / 🟢 확정 / 🔴 기각 / ⚪ 대체됨).

| 후보 | 상태 | 판단 근거 / 트레이드오프 / 깨지는 시점 | 사용자 피드백 |
|---|---|---|---|
| sentence-transformers | 🟢 확정 | 로컬 임베딩 생성 — Claude/외부 API 호출 비용·지연 없이 배치 인덱싱 가능. 트레이드오프: GPU 없는 ARM 환경에서 추론 속도 느림, 임베딩 품질이 상용 API보다 낮을 수 있음. 노트 수가 수만 건 이상으로 늘면 배치 시간이 부담될 수 있음 | 확정 |
| GitPython | 🟢 확정 | vault-ingest에서 git diff/commit 자동화에 필요. 대안인 셸 커맨드 직접 호출보다 에러 핸들링이 수월함 | 확정 |
| python-frontmatter | 🟢 확정 | 마크다운 frontmatter(YAML 메타데이터) 파싱 표준 라이브러리, 직접 파서 구현보다 안전 | 확정 |
| Alembic | 🟢 확정 | PostgreSQL 스키마 마이그레이션 관리. 노트/링크 그래프 스키마가 초기에 자주 바뀔 가능성이 높아 필요 | 확정 |
| mcp (Python SDK) | 🟢 확정 | vault-api를 MCP 서버로 감싸 Claude Code 등에서 도구 호출로 접근하기 위해 필요. 공식 SDK 사용이 프로토콜 직접 구현보다 안전 | 확정 |

### 외부 데이터 소스
해당 없음 — Mimir 외부 의존성은 LLM API(Claude, Grok)뿐입니다. 위 "공통 스택"에 포함되어 있어 별도 표로 관리하지 않습니다.

> 위 5개 항목이 모두 🟢 확정되어, 상세 가이드를 `.claude/skills/{스택명}/SKILL.md`로 분리했습니다(스택 판단 원칙 4번):
> `.claude/skills/sentence-transformers/SKILL.md`, `.claude/skills/gitpython/SKILL.md`,
> `.claude/skills/python-frontmatter/SKILL.md`, `.claude/skills/alembic/SKILL.md`,
> `.claude/skills/mcp-python-sdk/SKILL.md`. 각 결정의 트레이드오프/설계가 깨지는 시점/선택 이유는
> `DESIGN_NOTES.md`에 기록했습니다.

---

## 스택 판단 원칙 (공통, 프로젝트별 수정 불필요)
1. "프로젝트 스택 > 공통 스택"에 적힌 것은 항상 사용 가능한 것으로 간주하고 별도 확인 없이 사용합니다.
2. "테스트/품질 도구"에 적힌 값을 그대로 사용합니다.
3. "확장 스택"은 사용자가 미리 정해두는 목록이 아니라, OVERVIEW.md를 분석해서 Claude가
   WORKFLOW.md "의사결정 사이클"에 따라 직접 판단하고 채우는 영역입니다.
4. 새로 `🟢 확정`된 확장 스택은 `.claude/skills/{스택명}/SKILL.md`로 분리합니다.
   관련 작업을 할 때만 로드되어, 안 쓰는 스택 규칙이 매 세션 컨텍스트를 차지하지 않습니다.
5. 위에 없는 세부 사항(라이브러리 버전 등)이 필요하면, 프로젝트 내 실제 설정 파일
   (`pyproject.toml`, `requirements.txt`, `.python-version` 등)을 직접 확인해서 판단합니다.