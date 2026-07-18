import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas.response import GemmaAnalysis


class GemmaService:
    """
    Real Gemma integration with a safe fallback.

    The service tries to load the model settings from the backend .env file,
    then calls the configured model for structured analysis. If the API key is
    unavailable or the call fails, it falls back to a deterministic heuristic
    so the workflow continues to operate during demos and local testing.
    """

    BASE_DIR = Path(__file__).resolve().parents[1]
    ENV_PATH = BASE_DIR / ".env"
    SYSTEM_PROMPT_PATH = BASE_DIR / "prompts" / "system_prompt.txt"
    REPORT_PROMPT_PATH = BASE_DIR / "prompts" / "report_prompt.txt"

    @staticmethod
    def _load_env() -> None:
        load_dotenv(GemmaService.ENV_PATH)

    @staticmethod
    def _read_prompt(path: Path, fallback: str) -> str:
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                return content
        return fallback

    @staticmethod
    def _json_from_text(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        return json.loads(cleaned)

    @staticmethod
    def _fallback_analyze(payload: dict[str, Any]) -> dict[str, Any]:
        triggered_rules = payload.get("triggered_rules", [])
        amount = float(payload.get("record", {}).get("amount", 0) or 0)
        record_type = payload.get("record_type", "Transaction")

        score = min(95, 45 + (len(triggered_rules) * 8) + (1 if amount >= 100000 else 0))
        if score >= 80:
            risk_category = "fraud"
        elif score >= 55:
            risk_category = "high"
        else:
            risk_category = "medium"

        explanation = (
            f"{record_type} record is flagged because the following risk signals were triggered: "
            f"{', '.join(triggered_rules) or 'rule-based anomaly detection'}. "
            f"The amount of ₹{amount:,.0f} is materially suspicious for the associated business context."
        )

        recommended_action = (
            "escalate_to_compliance"
            if score >= 80
            else "manual_review"
        )

        return {
            "risk_score": int(score),
            "risk_category": risk_category,
            "explanation": explanation,
            "recommended_action": recommended_action,
        }

    @staticmethod
    def _build_analysis_prompt(payload: dict[str, Any]) -> str:
        record_type = payload.get("record_type", "Transaction")
        record = payload.get("record", {})
        rules = payload.get("triggered_rules", [])

        return (
            f"You are an AI fraud investigation assistant for Indian finance operations. "
            f"Explain why the flagged {record_type.lower()} record should be investigated. "
            "Use the supplied record and rules only. "
            "Return valid JSON only with the keys: risk_score, risk_category, explanation, recommended_action.\n\n"
            f"Triggered rules: {json.dumps(rules, ensure_ascii=False)}\n\n"
            f"Record: {json.dumps(record, ensure_ascii=False)}"
        )

    @staticmethod
    def analyze(payload: dict[str, Any]) -> dict[str, Any]:
        GemmaService._load_env()

        api_key = os.getenv("GEMMA_API_KEY", "").strip()
        model_name = os.getenv("MODEL_NAME", "gemma-3n-e4b-it").strip()

        if not api_key or api_key == "YOUR_API_KEY":
            return GemmaService._fallback_analyze(payload)

        try:
            client = genai.Client(api_key=api_key)
            system_instruction = GemmaService._read_prompt(
                GemmaService.SYSTEM_PROMPT_PATH,
                "You are a finance risk analyst. Respond in JSON only.",
            )

            response = client.models.generate_content(
                model=model_name,
                contents=GemmaService._build_analysis_prompt(payload),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=GemmaAnalysis,
                ),
            )

            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if hasattr(parsed, "model_dump"):
                    data = parsed.model_dump()
                else:
                    data = dict(parsed)
            else:
                text = getattr(response, "text", None)
                if not text:
                    raise ValueError("No text returned from model response")
                data = GemmaService._json_from_text(text)

            return {
                "risk_score": int(data.get("risk_score", 0)),
                "risk_category": str(data.get("risk_category", "medium")),
                "explanation": str(data.get("explanation", "No explanation returned")),
                "recommended_action": str(
                    data.get("recommended_action", "manual_review")
                ),
            }

        except Exception:
            return GemmaService._fallback_analyze(payload)

    @staticmethod
    def generate_report(records) -> str:
        GemmaService._load_env()

        api_key = os.getenv("GEMMA_API_KEY", "").strip()
        model_name = os.getenv("MODEL_NAME", "gemma-3n-e4b-it").strip()

        if not api_key or api_key == "YOUR_API_KEY":
            total = len(records)
            high = sum(1 for record in records if record.gemmaAnalysis.risk_score >= 80)
            medium = sum(1 for record in records if 50 <= record.gemmaAnalysis.risk_score < 80)
            low = sum(1 for record in records if record.gemmaAnalysis.risk_score < 50)

            return (
                f"The uploaded dataset produced {total} flagged records. "
                f"High-risk findings: {high}. Medium-risk findings: {medium}. "
                f"Low-risk findings: {low}. The dominant signals point to unusual transaction behavior, "
                "mismatched invoice linkage, and outlier financial amounts that warrant investigation."
            )

        try:
            client = genai.Client(api_key=api_key)
            report_prompt = GemmaService._read_prompt(
                GemmaService.REPORT_PROMPT_PATH,
                "Summarize the flagged compliance findings for an executive audience.",
            )

            response = client.models.generate_content(
                model=model_name,
                contents=(
                    f"{report_prompt}\n\n"
                    f"Records: {json.dumps([record.model_dump() for record in records], ensure_ascii=False)}"
                ),
                config=types.GenerateContentConfig(
                    system_instruction="You are a compliance report writer. Provide a concise executive summary in plain English.",
                    temperature=0.2,
                    response_mime_type="text/plain",
                ),
            )

            return getattr(response, "text", "") or "Executive summary unavailable."

        except Exception:
            total = len(records)
            high = sum(1 for record in records if record.gemmaAnalysis.risk_score >= 80)
            medium = sum(1 for record in records if 50 <= record.gemmaAnalysis.risk_score < 80)
            low = sum(1 for record in records if record.gemmaAnalysis.risk_score < 50)

            return (
                f"The uploaded dataset produced {total} flagged records. "
                f"High-risk findings: {high}. Medium-risk findings: {medium}. "
                f"Low-risk findings: {low}. The dominant signals point to unusual transaction behavior, "
                "mismatched invoice linkage, and outlier financial amounts that warrant investigation."
            )
