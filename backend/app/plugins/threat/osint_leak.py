"""
OSINT Leak Plugin — searches data breaches and leaks via Leakosint API.

Integrates with INDRA2's plugin system. Auto-registers when placed in
backend/app/plugins/threat/. Results appear in the dashboard GUI and
terminal views alongside other plugins.

API:  POST https://leakosintapi.com/
Auth: token in JSON body
"""

import logging
import os
from typing import Any

import httpx

from app.plugins.base import OSINTPlugin, PluginResult

logger = logging.getLogger(__name__)

# ── Known breach-emoji mapping ────────────────────────────────────────
BREACH_EMOJIS: dict[str, str] = {
    "1win": "🎲", "bigbasket": "🧃", "boat": "🛥",
    "truecaller": "🇮🇳", "facebook": "📘", "instagram": "📸",
    "linkedin": "💼", "twitter": "🐦", "telegram": "✈️",
    "adobe": "🎨", "canva": "🖼", "dropbox": "📦",
}


def _breach_emoji(name: str) -> str:
    """Pick an emoji for a breach database name."""
    key = name.lower().replace(" ", "").replace("-", "")
    for prefix, emoji in BREACH_EMOJIS.items():
        if prefix in key or key.startswith(prefix):
            return emoji
    return "📂"


def _load_token() -> str:
    """Load API token from env var."""
    return os.environ.get("TELEGRAM_OSINT_API_KEY", "")


class OSINTLeakPlugin(OSINTPlugin):
    plugin_id = "osint-leak"
    name = "OSINT Leak"
    category = "threat"
    description = "Search across data breaches and leaks for emails, phones, names, IPs, and usernames"
    input_types = ["email", "phone", "username", "name", "ip"]
    icon = "💦"

    API_URL = "https://leakosintapi.com/"
    TIMEOUT = 30

    def __init__(self):
        super().__init__()
        self._token = _load_token()
        if not self._token:
            logger.warning("Leakosint API token not found in TELEGRAM_OSINT_API_KEY")
        else:
            logger.info("Leakosint API token loaded")

    async def run(self, target: str) -> PluginResult:
        if not self._token:
            return PluginResult(
                plugin_id=self.plugin_id, plugin_name=self.name,
                category=self.category, target=target,
                status="failed",
                error="API token not configured. Set TELEGRAM_OSINT_API_KEY in .env",
            )

        payload = {
            "token": self._token,
            "request": target,
            "limit": 100,
            "lang": "en",
        }

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.post(self.API_URL, json=payload, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    # Check for API errors
                    if "Error code" in data:
                        err = data.get("Error code", "Unknown error")
                        logger.warning("Leakosint API error: %s", err)
                        return PluginResult(
                            plugin_id=self.plugin_id, plugin_name=self.name,
                            category=self.category, target=target,
                            status="failed", error=f"API error: {err}",
                        )
                    return self._format_results(target, data)

                logger.warning("Leakosint API returned HTTP %d", resp.status_code)
                return PluginResult(
                    plugin_id=self.plugin_id, plugin_name=self.name,
                    category=self.category, target=target,
                    status="failed",
                    error=f"API returned HTTP {resp.status_code}",
                )

        except httpx.TimeoutException:
            return PluginResult(
                plugin_id=self.plugin_id, plugin_name=self.name,
                category=self.category, target=target,
                status="failed", error="API timed out after 30s",
            )
        except Exception as exc:
            logger.exception("Leakosint plugin error for %s", target)
            return PluginResult(
                plugin_id=self.plugin_id, plugin_name=self.name,
                category=self.category, target=target,
                status="failed", error=str(exc),
            )

    def _format_results(self, target: str, data: dict) -> PluginResult:
        """Convert the Leakosint API response into gui_data + terminal_data.

        Response format:
        {
          "List": {
            "BreachName": {
              "InfoLeak": "description",
              "Data": [{ col: val, ... }, ...],
              "NumOfResults": N
            }
          }
        }
        """
        db_list = data.get("List", {})
        if not db_list:
            return PluginResult(
                plugin_id=self.plugin_id, plugin_name=self.name,
                category=self.category, target=target,
                gui_data={"Target": target, "Status": "No breaches found"},
                terminal_data=f"[+] No breaches found for {target}",
            )

        # Filter out "No results found" pseudo-entry
        databases = {k: v for k, v in db_list.items() if k != "No results found"}
        breach_count = len(databases)
        total_records = sum(
            db.get("NumOfResults", len(db.get("Data", [])))
            for db in databases.values()
        )

        # ── GUI data ──────────────────────────────────────────────────
        gui_data: dict[str, Any] = {
            "Target": target,
            "Breaches Found": breach_count,
            "Total Records": total_records,
        }

        for db_name, db_data in databases.items():
            emoji = _breach_emoji(db_name)
            records = db_data.get("Data", [])
            info = db_data.get("InfoLeak", "")[:120]

            # Build a summary from the first record's key fields
            if records and isinstance(records, list) and len(records) > 0:
                first = records[0]
                summary_parts = []
                for key in ["Email", "Phone", "Telephone", "FullName", "FirstName",
                            "LastName", "Name", "IP", "City", "Country", "Password",
                            "UserName", "Login"]:
                    val = first.get(key, first.get(key.lower(), ""))
                    if val:
                        summary_parts.append(f"{key}={val}")
                        break
                label = f"{emoji} {db_name}"
                if summary_parts:
                    gui_data[label] = ", ".join(summary_parts)
                else:
                    gui_data[label] = f"{len(records)} records exposed"
            else:
                gui_data[f"{emoji} {db_name}"] = "Data exposed"

        gui_data["Source"] = "leakosintapi.com"

        # ── Terminal data ─────────────────────────────────────────────
        terminal_lines = [
            f"[+] OSINT Leak Search — {target}",
            f"[+] Breaches found: {breach_count}  |  Total records: {total_records}",
            f"{'=' * 55}",
        ]

        for db_name, db_data in databases.items():
            emoji = _breach_emoji(db_name)
            terminal_lines.append(f"\n{emoji}  {db_name}")

            info = db_data.get("InfoLeak", "")
            if info:
                terminal_lines.append(f"   {info[:500]}")

            records = db_data.get("Data", [])
            if isinstance(records, list):
                for rec in records[:3]:  # Show up to 3 records per breach
                    for key, value in rec.items():
                        if value:
                            terminal_lines.append(f"   {key}: {value}")
                if len(records) > 3:
                    terminal_lines.append(f"   ... and {len(records) - 3} more records")

        return PluginResult(
            plugin_id=self.plugin_id, plugin_name=self.name,
            category=self.category, target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
