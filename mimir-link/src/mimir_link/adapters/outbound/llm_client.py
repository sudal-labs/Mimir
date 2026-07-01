"""LlmLinkClient 구현체 — Anthropic Claude API로 연결 제안을 생성한다."""
import json
import os

import anthropic

from mimir_link.domain.models import LinkSuggestion
from mimir_link.ports.outbound import LlmLinkClient

LINK_SUGGESTION_PROMPT = """\
아래 '소스 노트'와 '후보 노트 목록'을 읽고, 소스 노트와 연결할 가치가 있는 후보를 JSON 배열로 반환하라.

규칙:
1. 주제·개념·인과 관계에서 실질적인 연결이 있을 때만 제안한다.
2. 관련도가 낮은 후보는 포함하지 않는다.
3. 각 항목: {{"targetNoteId": "...", "reason": "한 문장", "confidence": 0.0~1.0}}

소스 노트:
{source}

후보 노트:
{candidates}

JSON 배열만 출력하라. 설명 없음.
"""

CONFIDENCE_THRESHOLD = 0.7


class AnthropicLinkClient(LlmLinkClient):
    """Claude API를 호출해 연결 제안 JSON을 파싱한다."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self._model = os.getenv("ANTHROPIC_LINK_MODEL", "claude-opus-4-6")

    async def suggest_links(
        self,
        source_content: str,
        candidate_notes: list[dict],
    ) -> list[LinkSuggestion]:
        """Claude에게 연결 제안을 요청하고 파싱 결과를 반환한다."""
        if not candidate_notes:
            return []

        candidates_text = "\n".join(
            f"- noteId={c['noteId']}, filePath={c['filePath']}: {c.get('snippet', '')}"
            for c in candidate_notes
        )
        prompt = LINK_SUGGESTION_PROMPT.format(
            source=source_content[:2000],
            candidates=candidates_text,
        )

        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text
        return self._parse_suggestions(raw_text, candidate_notes)

    def _parse_suggestions(
        self,
        raw_text: str,
        candidate_notes: list[dict],
    ) -> list[LinkSuggestion]:
        """LLM 응답 JSON을 LinkSuggestion 목록으로 변환한다. 파싱 실패 시 빈 리스트 반환."""
        candidate_index = {c["noteId"]: c for c in candidate_notes}
        try:
            items = json.loads(raw_text)
        except json.JSONDecodeError:
            return []

        suggestions: list[LinkSuggestion] = []
        for item in items:
            target_note_id = item.get("targetNoteId", "")
            confidence = float(item.get("confidence", 0.0))
            if confidence < CONFIDENCE_THRESHOLD:
                continue
            candidate = candidate_index.get(target_note_id)
            if not candidate:
                continue
            suggestions.append(LinkSuggestion(
                source_note_id="",  # LinkService에서 주입
                target_note_id=target_note_id,
                target_file_path=candidate.get("filePath", ""),
                reason=item.get("reason", ""),
                confidence=confidence,
            ))

        return suggestions
