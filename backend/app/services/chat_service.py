"""
TRINETRA — AI Chatbot Service

Lightweight wrapper around the Google Gemini API. Acts as an in-app
SOC-analyst assistant: explains the dashboard, and when the frontend
passes along current scan/target data as `context`, can interpret
findings and generate structured investigation reports.
"""

import httpx
from app.core.config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

BASE_SYSTEM_PROMPT = (
    "You are the TRINETRA Assistant, an in-app SOC-analyst-style helper for the "
    "TRINETRA OSINT Dashboard. TRINETRA lets users search a target (domain, email, "
    "IP, username, phone) and runs OSINT plugins (infrastructure, threat, advanced "
    "categories) against it, shows results on a map/graph, and supports 'Watches' "
    "that re-check a target periodically and alert on changes. Be concise, "
    "friendly, and practical. Help users understand features, interpret results, "
    "and navigate the dashboard. If asked something unrelated, answer briefly and "
    "steer back to being useful."
)

REPORT_INSTRUCTIONS = (
    "\n\nThe user's current investigation data is provided below (live OSINT scan "
    "results they are looking at right now). Use it to answer questions about the "
    "target, and if the user asks for a report, summary, or analysis, produce a "
    "well-structured SOC-analyst investigation report in markdown with these "
    "sections: **Target Overview**, **Key Findings** (grouped by category), "
    "**Risk Assessment**, and **Recommended Actions**. Base every claim only on "
    "the data given — do not invent findings that aren't present.\n\n"
    "=== CURRENT INVESTIGATION DATA ===\n{context}\n=== END DATA ==="
)


class ChatService:
    async def get_reply(
        self,
        message: str,
        history: list[dict] | None = None,
        context: str | None = None,
    ) -> str:
        if not settings.gemini_api_key:
            return (
                "Chatbot isn't configured yet — set GEMINI_API_KEY in your "
                "backend .env file to enable AI responses."
            )

        system_prompt = BASE_SYSTEM_PROMPT
        if context:
            # Cap context size to keep requests fast and cheap
            system_prompt += REPORT_INSTRUCTIONS.format(context=context[:8000])

        contents = []
        for turn in (history or [])[-10:]:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "contents": contents,
            "system_instruction": {"parts": [{"text": system_prompt}]},
        }
        url = GEMINI_URL.format(model=settings.gemini_model)

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "Sorry, I didn't get a response — try again."
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                return text or "Sorry, I didn't get a response — try again."
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300]
            return f"Chatbot service error ({e.response.status_code}): {detail}"
        except Exception:
            return "Chatbot service is temporarily unavailable. Please try again shortly."


chat_service = ChatService()