"""LlmSynthesizer 구현체 — Claude API로 검색 결과를 합성한다."""
import os

import anthropic

from mimir_api.domain.models import NoteRef
from mimir_api.ports.outbound import LlmSynthesizer

SYNTHESIS_PROMPT = """\
아래 참고 노트들을 바탕으로 질문에 한국어로 답하라.
답변 마지막에 근거로 사용한 노트 파일명을 나열하라.

질문: {query}

참고 노트:
{contexts}
"""


class AnthropicSynthesizer(LlmSynthesizer):
    """Claude API로 검색 컨텍스트를 합성해 자연어 답변을 생성한다."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self._model = os.getenv("ANTHROPIC_SYNTH_MODEL", "claude-opus-4-6")

    async def synthesize(self, query: str, contexts: list[NoteRef]) -> str:
        """contexts를 프롬프트에 삽입하고 Claude에게 답변을 요청한다."""
        context_text = "\n\n".join(
            f"[{ref.file_path or ref.note_id}]\n{ref.snippet}"
            for ref in contexts
        )
        prompt = SYNTHESIS_PROMPT.format(query=query, contexts=context_text)

        message = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
