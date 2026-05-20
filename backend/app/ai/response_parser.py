import json
import re
from typing import Any

from app.ai.base import LLMResponse
from app.core.logging import get_logger
from app.domain.models.analysis import StaticAnalysisResult
from app.domain.models.review import AIFinding, AIReview

logger = get_logger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


class AIResponseParser:
    """
    Parses the raw LLM text output into a structured AIReview.

    Handles three formats the LLM might return:
    1. Bare JSON object  (ideal)
    2. JSON wrapped in a markdown code fence
    3. Unstructured text  (fallback — wraps the raw text as the summary)
    """

    def parse(self, response: LLMResponse, analysis: StaticAnalysisResult) -> AIReview:
        raw = response.content.strip()
        data = self._extract_json(raw)

        if data is None:
            logger.warning(
                "ai.response.parse_fallback",
                provider=response.provider,
                content_preview=raw[:200],
            )
            return self._fallback(response, raw)

        try:
            return self._build_review(data, response, analysis)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "ai.response.schema_mismatch",
                provider=response.provider,
                error=str(exc),
            )
            return self._fallback(response, raw)

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        # 1. Bare JSON (ideal path)
        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass

        # 2. JSON inside a markdown code fence
        match = _JSON_FENCE_RE.search(text)
        if match:
            try:
                return json.loads(match.group(1).strip())  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # 3. First {...} block embedded in surrounding text (common with small local models)
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start : brace_end + 1])  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        return None

    def _build_review(
        self,
        data: dict[str, Any],
        response: LLMResponse,
        analysis: StaticAnalysisResult,
    ) -> AIReview:
        raw_findings = data.get("findings")
        if not isinstance(raw_findings, list):
            raw_findings = []
        findings = [
            AIFinding(
                rule_id=str(f.get("rule_id") or "ai_detected"),
                explanation=str(f.get("explanation") or f.get("message") or ""),
                suggestion=f.get("suggestion") or f.get("fix") or None,
            )
            for f in raw_findings
            if isinstance(f, dict) and (f.get("explanation") or f.get("message"))
        ]

        # If the LLM returned no findings but static analysis found some,
        # synthesize minimal AI findings from the static ones so the
        # response is never empty.
        if not findings and analysis.findings:
            findings = [
                AIFinding(
                    rule_id=sf.rule_id,
                    explanation=sf.message,
                    suggestion=sf.suggestion,
                )
                for sf in analysis.findings
            ]

        return AIReview(
            summary=str(data.get("summary", "Review complete.")),
            improved_query=data.get("improved_query") or None,
            findings=findings,
            educational_note=data.get("educational_note") or None,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

    def _fallback(self, response: LLMResponse, raw_text: str) -> AIReview:
        return AIReview(
            summary=raw_text[:1000],
            findings=[],
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
