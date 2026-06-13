import logging
import re
from app.plugins.base import OSINTPlugin, PluginResult
import httpx

logger = logging.getLogger(__name__)


class SocialRadarPlugin(OSINTPlugin):
    plugin_id = "social-radar"
    name = "Social Radar"
    category = "advanced"
    description = "Social media footprint, cross-platform presence"
    input_types = ["username", "name", "email"]
    icon = "📊"

    SOCIAL_SITES = {
        "LinkedIn": "https://www.linkedin.com/in/{username}",
        "Twitter/X": "https://twitter.com/{username}",
        "Facebook": "https://www.facebook.com/{username}",
        "Instagram": "https://www.instagram.com/{username}/",
        "YouTube": "https://www.youtube.com/@{username}",
        "Reddit": "https://www.reddit.com/user/{username}",
        "GitHub": "https://github.com/{username}",
        "Medium": "https://medium.com/@{username}",
    }

    def _extract_username(self, target: str) -> str:
        """Extract a username from the target.
        
        - If it's an email (contains @), extract the local part before @.
        - Otherwise use the target as-is.
        """
        if "@" in target:
            local = target.split("@", 1)[0].strip()
            # Filter out characters that won't work as usernames
            # (e.g., dots at start/end, special chars)
            local = re.sub(r"[^a-zA-Z0-9_.-]", "", local)
            return local if local else target
        return target

    async def run(self, target: str) -> PluginResult:
        username = self._extract_username(target)
        is_email = "@" in target
        domain = target.split("@", 1)[1] if is_email else None

        found = []
        not_found = []

        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            for site, url_tpl in self.SOCIAL_SITES.items():
                url = url_tpl.replace("{username}", username)
                try:
                    resp = await client.head(url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code < 400:
                        found.append(site)
                    else:
                        not_found.append(site)
                except Exception as e:
                    logger.debug("Social check failed for %s on %s: %s", target, site, e)
                    not_found.append(site)

        score = round((len(found) / len(self.SOCIAL_SITES)) * 100)

        gui_data = {
            "Target": target,
            "Searched As": username,
            "Profiles Found": len(found),
            "Social Score": f"{score}%",
            "Platforms Checked": len(self.SOCIAL_SITES),
            "Found On": ", ".join(found) if found else "None",
        }

        if is_email and domain:
            gui_data["Email Domain"] = domain

        terminal_header = f"Social Radar Report — {target}"
        if is_email:
            terminal_header += f"\n[+] Extracted username: {username}"
            terminal_header += f"\n[+] Email domain: {domain}"

        terminal = f"""{terminal_header}
Profiles Found: {len(found)}/{len(self.SOCIAL_SITES)}
Social Score: {score}%
---
Found: {', '.join(found) if found else 'None'}
Not found: {', '.join(not_found) if not_found else 'None'}"""

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data=terminal,
        )
