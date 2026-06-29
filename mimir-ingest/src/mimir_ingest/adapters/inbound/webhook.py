"""GitHub / 커스텀 git push webhook 수신 라우터"""
import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from mimir_ingest.ports.inbound import IngestUseCase

router = APIRouter(tags=["webhook"])

# main.py의 lifespan에서 주입한다.
_ingest_use_case: IngestUseCase | None = None


def set_ingest_use_case(use_case: IngestUseCase) -> None:
    """애플리케이션 시작 시 의존성을 주입한다."""
    global _ingest_use_case
    _ingest_use_case = use_case


class GitPushPayload(BaseModel):
    """git push webhook 페이로드

    JSON 필드명: camelCase (API 컨벤션)
    Python 필드명: snake_case (코드 컨벤션)
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    repo_path: str
    """컨테이너 내부 vault 마운트 경로 (예: '/vault')"""

    before_hash: str
    """push 직전 HEAD 커밋 SHA"""

    after_hash: str
    """push 직후 HEAD 커밋 SHA"""


@router.post("/git")
async def handle_git_push(
    payload: GitPushPayload,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> dict:
    """git push 이벤트를 수신해 변경된 노트를 파싱하고 이벤트를 발행한다."""
    _verify_webhook_secret(x_webhook_secret)

    if _ingest_use_case is None:
        raise HTTPException(status_code=503, detail="서비스 초기화 중입니다.")

    events = await _ingest_use_case.handle_git_push(
        repo_path=payload.repo_path,
        before_hash=payload.before_hash,
        after_hash=payload.after_hash,
    )
    return {"publishedEvents": len(events)}


def _verify_webhook_secret(provided: str | None) -> None:
    """WEBHOOK_SECRET 환경 변수가 설정된 경우 요청 헤더 값을 검증한다."""
    expected_secret = os.getenv("WEBHOOK_SECRET", "")
    if not expected_secret:
        return
    if provided != expected_secret:
        raise HTTPException(status_code=401, detail="Webhook secret이 올바르지 않습니다.")
