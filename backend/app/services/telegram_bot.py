"""
Telegram OSINT Leak Bot — integrated into INDRA2.

Architecture:
  Telegram User → Telegram Bot → OSINT API (your data source) → Formatted Response → User

Auto-detects query types: email, phone, IP, name/username.
Wired into FastAPI lifespan (starts/stops with the server).
"""

import json
import logging
import re
from typing import Any, Optional

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger("trinetra.telegram")

# ── Source emoji mapping ──────────────────────────────────────────────
SOURCE_EMOJIS: dict[str, str] = {
    "boat": "🛥",
    "boatlifestyle": "🛥",
    "bigbasket": "🧃",
    "1win": "🎲",
    "truecaller": "🇮🇳",
    "breached": "🕵",
    "breachedforum": "🕵",
    "swachhmanch": "🧹",
    "swachh": "🧹",
    "facebook": "📘",
    "instagram": "📸",
    "vkontakte": "🌟",
    "vk": "🌟",
    "telegram": "✈️",
    "twitter": "🐦",
    "linkedin": "💼",
    "adobe": "🎨",
    "canva": "🖼",
    "myspace": "🎵",
    "dropbox": "📦",
    "haveibeenpwned": "🔍",
    "hibp": "🔍",
}

# ── Field-to-emoji mapping ───────────────────────────────────────────
FIELD_EMOJIS: dict[str, str] = {
    "email": "📩",
    "mail": "📩",
    "e-mail": "📩",
    "telephone": "📞",
    "phone": "📞",
    "mobile": "📞",
    "phone_number": "📞",
    "password": "🔑",
    "pass": "🔑",
    "encrypted_password": "🔐",
    "password_hash": "🔐",
    "hash": "🔐",
    "ip": "🎯",
    "ip_address": "🎯",
    "ipaddress": "🎯",
    "name": "👤",
    "full_name": "👤",
    "fullname": "👤",
    "first_name": "👤",
    "firstname": "👤",
    "surname": "👤",
    "last_name": "👤",
    "lastname": "👤",
    "nick": "👤",
    "nickname": "👤",
    "username": "👤",
    "address": "🏘️",
    "adres": "🏘️",
    "adress": "🏘️",
    "city": "🌃",
    "town": "🌃",
    "postal_code": "🏤",
    "postcode": "🏤",
    "zip": "🏤",
    "pincode": "🏤",
    "pin_code": "🏤",
    "region": "🗺️",
    "state": "🗺️",
    "province": "🗺️",
    "country": "🗾",
    "landmark": "🗼",
    "last_activity": "📆",
    "lastactivity": "📆",
    "last_login": "📆",
    "lastlogin": "📆",
    "registration_date": "📆",
    "date_of_registration": "📆",
    "date_registered": "📆",
    "date_of_birth": "🎂",
    "dob": "🎂",
    "birthday": "🎂",
    "tags": "🏷️",
    "tag": "🏷️",
    "sum": "💸",
    "amount": "💸",
    "total": "💸",
    "orders": "📦",
    "order_count": "📦",
    "number_of_orders": "📦",
    "currency": "💶",
    "operator": "📡",
    "mobile_operator": "📡",
    "carrier": "📡",
    "gender": "⚤",
    "age": "📅",
    "occupation": "💼",
    "job": "💼",
    "company": "🏢",
    "website": "🌐",
    "url": "🌐",
    "social": "🔗",
    "profile": "🔗",
    "facebook_id": "📘",
    "twitter_id": "🐦",
    "instagram_id": "📸",
}


def _normalize(text: str) -> str:
    """Lowercase, strip, and collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_input_type(query: str) -> str:
    """Auto-detect what type of query the user sent.

    Returns one of: 'email', 'phone', 'ip', 'domain', 'name'
    """
    q = query.strip()

    # Email — must contain @ with a proper domain
    if re.match(r"^[\w.%-]+@[\w.-]+\.[a-zA-Z]{2,}$", q):
        return "email"
    # @domain.tld — domain-wide search
    if re.match(r"^@[\w.-]+\.[a-zA-Z]{2,}$", q):
        return "email"

    # Phone — starts with + or is all digits with 7+ digits
    cleaned = re.sub(r"[\s\-()]", "", q)
    if cleaned.startswith("+") or (cleaned.isdigit() and len(cleaned) >= 7):
        return "phone"

    # IP address
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", q):
        return "ip"

    # Domain (without protocol)
    if re.match(r"^[\w-]+\.[a-zA-Z]{2,}$", q) and " " not in q:
        return "domain"

    # Default — name, username, or composite query
    return "name"


def _source_emoji(source: str) -> str:
    """Pick an emoji for a breach/leak source name."""
    key = _normalize(source).replace(" ", "").replace("-", "").replace(".", "")
    for prefix, emoji in SOURCE_EMOJIS.items():
        if prefix in key or key.startswith(prefix):
            return emoji
    # Fallback — pick based on first letter
    first = source.strip()[0].upper()
    return {
        "A": "🔴", "B": "🟠", "C": "🟡", "D": "🟢", "E": "🔵",
        "F": "🟣", "G": "🟤", "H": "⚫", "I": "⚪", "J": "🔶",
        "K": "🔷", "L": "🟥", "M": "🟧", "N": "🟨", "O": "🟩",
        "P": "🟦", "Q": "🟪", "R": "🟫", "S": "⬛", "T": "⬜",
        "U": "🔶", "V": "🔷", "W": "🟠", "X": "🔴", "Y": "🟣", "Z": "🟤",
    }.get(first, "📂")


def _field_emoji(key: str) -> str:
    """Pick an emoji for a data field name."""
    k = _normalize(key).replace(" ", "_").replace("-", "_")
    for name, emoji in FIELD_EMOJIS.items():
        if name in k or k.endswith(name):
            return emoji
    return "•"


def _escape_md(text: str) -> str:
    """Escape Markdown special characters."""
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


class TelegramBotService:
    """Telegram OSINT Leak Bot integrated with INDRA2."""

    def __init__(self, token: str, api_url: str, api_key: str):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.application: Optional[Application] = None

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def start(self) -> None:
        """Initialize and start polling."""
        self.application = Application.builder().token(self.token).build()

        # Register handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_query)
        )

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram OSINT Bot started — awaiting queries")

    async def stop(self) -> None:
        """Shut down polling."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram OSINT Bot stopped")

    # ── Command handlers ──────────────────────────────────────────────

    @staticmethod
    async def _cmd_start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        """Welcome message."""
        await update.message.reply_text(
            "🔍 *OSINT LEAK BOT*\n\n"
            "I search for leaked data across multiple breach databases.\n\n"
            "Simply send me what you want to look up:\n\n"
            "📧 `user@domain.com` — Search by email\n"
            "📱 `+919876543210` — Search by phone\n"
            "👤 `John Doe` — Search by name / username\n"
            "📍 `192.168.1.1` — Search by IP\n\n"
            "Use /help for the full command list.",
            parse_mode="MarkdownV2",
        )

    @staticmethod
    async def _cmd_help(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
        """Detailed help."""
        await update.message.reply_text(
            "🔍 *OSINT LEAK BOT — Available Searches*\n\n"
            "📧 *Search by email*\n"
            "├ `user@domain.com` — Full email search\n"
            "├ `@domain.com` — Domain-wide search\n\n"
            "👤 *Search by name or nick*\n"
            "├ `John` — First name\n"
            "├ `John Doe` — Full name\n"
            "└ `johndoe` — Username\n\n"
            "📱 *Search by phone*\n"
            "├ `+919876543210` — International format\n"
            "└ `9876543210` — Local format\n\n"
            "📍 *Search by IP*\n"
            "└ `192.168.1.1` — IPv4 address\n\n"
            "🌐 *Search by domain*\n"
            "└ `example.com` — Domain lookup\n\n"
            "⚡ *Composite queries are supported too!*\n"
            "├ `John 79002206090`\n"
            "├ `user@domain.com 123qwe`\n"
            "└ `ShadowPlayer228 example@gmail.com`\n\n"
            "_Just type anything and I'll figure it out._",
            parse_mode="MarkdownV2",
        )

    # ── Query handler ─────────────────────────────────────────────────

    async def _handle_query(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle a text message — detect type, call API, format response."""
        query = update.message.text.strip()
        if not query:
            return

        input_type = detect_input_type(query)
        logger.info("Telegram query: type=%s query=%s", input_type, query)

        # Tell Telegram we're typing
        await update.message.chat.send_action(action="typing")

        try:
            data = await self._call_api(query, input_type)

            if data is None:
                await update.message.reply_text(
                    "⚠️ *Could not reach the OSINT API.*\n"
                    "Please check the API configuration and try again later.",
                    parse_mode="MarkdownV2",
                )
                return

            # Check for API-level errors
            if isinstance(data, dict) and data.get("status") == "error":
                err_msg = data.get("message", "Unknown error")
                await update.message.reply_text(
                    f"⚠️ *OSINT API Error*\n"
                    f"`{_escape_md(err_msg)}`\n\n"
                    "Your API key may have reached its quota or expired.",
                    parse_mode="MarkdownV2",
                )
                return

            await self._send_results(update, query, data, input_type)

        except Exception as exc:
            logger.exception("Error processing Telegram query")
            await update.message.reply_text(
                "⚠️ *Error processing your request.*\n"
                f"`{_escape_md(str(exc))}`\n\n"
                "Please try again later.",
                parse_mode="MarkdownV2",
            )

    # ── Type mapping ────────────────────────────────────────────────────

    _API_TYPE_MAP: dict[str, str] = {
        "email": "email",
        "phone": "phone",
        "ip": "ip",
        "name": "name",
        "domain": "url",
    }

    def _map_type(self, input_type: str) -> str:
        """Map our internal input type to the OSINT API type."""
        return self._API_TYPE_MAP.get(input_type, "name")

    # ── API client ────────────────────────────────────────────────────

    async def _call_api(self, query: str, input_type: str) -> Optional[Any]:
        """Call the OSINT Leak API.

        API spec:
          GET  https://osintleak.com/api/v1/search_api/
          Params: api_key, query, type, stealerlogs, dbleaks,
                  dbleaks2, search_option, meta
          Auth:   api_key as query parameter
          Header: User-Agent: OL-Python/1.0.2
        """
        if not self.api_url:
            logger.warning("TELEGRAM_OSINT_API_URL is not configured")
            return None

        params: dict[str, str | bool] = {
            "api_key": self.api_key,
            "query": query,
            "type": self._map_type(input_type),
            "stealerlogs": False,
            "dbleaks": True,
            "dbleaks2": False,
            "search_option": "quick",
            "meta": True,
        }

        headers = {
            "User-Agent": "OL-Python/1.0.2",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(self.api_url, params=params, headers=headers)

            if resp.status_code == 200:
                return resp.json()

            # Try to parse error message from response body
            try:
                err_data = resp.json()
                err_msg = err_data.get("message", f"HTTP {resp.status_code}")
            except Exception:
                err_msg = f"HTTP {resp.status_code}"

            logger.warning(
                "OSINT API returned %d for query=%s: %s",
                resp.status_code,
                query,
                err_msg,
            )
            return {"status": "error", "message": err_msg, "results": []}

    # ── Response formatting ───────────────────────────────────────────

    async def _send_results(
        self, update: Update, query: str, data: Any, input_type: str
    ) -> None:
        """Format and send the API response to the user."""
        # If data is a dict, try structured formatting
        if isinstance(data, dict):
            await self._format_structured(update, query, data)
        # If data is a list, treat each item as a leak result
        elif isinstance(data, list):
            await self._format_list(update, query, data)
        # Fallback — raw JSON
        else:
            text = f"🔎 *Request:* `{_escape_md(query)}`\n\n```json\n{data}\n```"
            await update.message.reply_text(text[:4000], parse_mode="MarkdownV2")

    async def _format_structured(
        self, update: Update, query: str, data: dict
    ) -> None:
        """Format a structured dict response — matches OSINT Leak API format.

        Expected API shape:
        {
          "status": "success",
          "results": [{ ... }, ...],
          "count": 8,
          "page": 1,
          "total_page": 1,
          "search_title": "QS:query:type",
          "result_id": "uuid",
          "sl_limited": false,
          "cached": "no",
          "censored": false
        }
        """
        # ── Metadata header ────────────────────────────────────────────
        results_count = data.get("count") or len(data.get("results", []))
        total_pages = data.get("total_page", 1)
        search_title = data.get("search_title", query)
        cached = data.get("cached", "no")
        censored = data.get("censored", False)

        header_lines = [
            f"🔎 *Request:* `{_escape_md(query)}`",
            f"📁 Results found: {results_count}",
        ]
        if total_pages > 1:
            header_lines.append(f"📄 Pages: {total_pages}")
        if cached == "yes":
            header_lines.append("💾 Cached result")
        if censored:
            header_lines.append("🔞 Results may be censored")

        header_lines.append(
            "\n🆓 Free version — subscribe to reduce token usage by 10x"
        )
        header_lines.append("🪞 Mirror: @MK_fanstatbot")

        await update.message.reply_text(
            "\n".join(header_lines), parse_mode="MarkdownV2"
        )

        # ── Result entries ─────────────────────────────────────────────
        results = data.get("results", [])

        if isinstance(results, list) and results:
            for result in results:
                msg = self._format_leak_entry(result)
                for chunk in _chunk_text(msg, 4000):
                    await update.message.reply_text(chunk, parse_mode="MarkdownV2")
        elif isinstance(results, dict):
            msg = self._format_leak_entry(results)
            for chunk in _chunk_text(msg, 4000):
                await update.message.reply_text(chunk, parse_mode="MarkdownV2")
        else:
            # Results is not a list/dict — could be a different structure.
            # Try dumping as raw JSON for debugging.
            raw = json.dumps(data, indent=2, ensure_ascii=False)
            if len(raw) > 3900:
                raw = raw[:3900] + "\n...\n(truncated)"
            await update.message.reply_text(
                f"📦 *Raw API response:*\n```json\n{raw}\n```",
                parse_mode="MarkdownV2",
            )

    async def _format_list(
        self, update: Update, query: str, items: list
    ) -> None:
        """Format a list response (each item is a leak/result)."""
        header = (
            f"🔎 *Request:* `{_escape_md(query)}`\n"
            f"📁 Number of results: {len(items)}\n"
        )
        await update.message.reply_text(header, parse_mode="MarkdownV2")

        for item in items:
            if isinstance(item, dict):
                msg = self._format_leak_entry(item)
            else:
                msg = f"• {item}"
            for chunk in _chunk_text(msg, 4000):
                await update.message.reply_text(chunk, parse_mode="MarkdownV2")

    def _format_leak_entry(self, leak: dict) -> str:
        """Format a single leak/breach entry into a Telegram message."""
        lines: list[str] = []

        # ── Title / source name ────────────────────────────────────────
        title = (
            leak.get("title")
            or leak.get("source")
            or leak.get("name")
            or leak.get("company")
            or leak.get("site")
            or "Unknown Source"
        )
        emoji = leak.get("emoji") or _source_emoji(title)
        lines.append(f"{emoji}*{_escape_md(title)}*")

        # ── Description ────────────────────────────────────────────────
        desc = (
            leak.get("description")
            or leak.get("desc")
            or leak.get("summary")
            or leak.get("info", "")
        )
        if desc:
            # Truncate long descriptions
            if len(desc) > 800:
                desc = desc[:797] + "..."
            lines.append(f"\n{desc}")

        # ── Data fields ────────────────────────────────────────────────
        fields = (
            leak.get("fields")
            or leak.get("data")
            or leak.get("details")
            or leak.get("attributes", {})
        )

        if isinstance(fields, dict):
            for key, value in fields.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    continue
                emoji_f = _field_emoji(key)
                label = key.replace("_", " ").replace("-", " ").title()
                val_str = str(value)
                # Truncate very long values
                if len(val_str) > 300:
                    val_str = val_str[:297] + "..."
                lines.append(f"\n{emoji_f}*{_escape_md(label)}:* {_escape_md(val_str)}")

        # ── Fallback — show all remaining keys as raw fields ─────────
        elif isinstance(fields, list):
            for item in fields:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if value:
                            emoji_f = _field_emoji(key)
                            lines.append(
                                f"\n{emoji_f}*{_escape_md(key)}:* {_escape_md(str(value))}"
                            )
                else:
                    lines.append(f"\n• {_escape_md(str(item))}")

        return "\n".join(lines)


def _chunk_text(text: str, max_len: int) -> list[str]:
    """Split long text into chunks at newline boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Find last newline within limit
        split = text.rfind("\n", 0, max_len)
        if split == -1:
            split = max_len
        chunks.append(text[:split])
        text = text[split:].lstrip("\n")
    return chunks
