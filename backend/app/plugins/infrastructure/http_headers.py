from app.plugins.base import OSINTPlugin, PluginResult
import httpx


class HTTPHeadersPlugin(OSINTPlugin):
    plugin_id = "http-headers"
    name = "HTTP Headers"
    category = "infrastructure"
    description = "Security headers, server info, cookies"
    input_types = ["domain"]
    icon = "📨"

    SECURITY_HEADERS = [
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
        "x-xss-protection",
        "access-control-allow-origin",
    ]

    async def run(self, target: str) -> PluginResult:
        try:
            url = f"https://{target}"
            async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as client:
                resp = await client.get(url)

            headers = dict(resp.headers)
            gui_data = {}
            terminal_lines = [f"HTTP Headers for {target}:", "---"]

            for h, v in headers.items():
                gui_data[h] = v
                terminal_lines.append(f"{h}: {v}")

            sec_present = [h for h in self.SECURITY_HEADERS if h in headers]
            sec_missing = [h for h in self.SECURITY_HEADERS if h not in headers]

            gui_data["Security Headers Present"] = len(sec_present)
            gui_data["Security Headers Missing"] = len(sec_missing)
            terminal_lines.extend([
                "---",
                f"Security Headers: {len(sec_present)}/{len(self.SECURITY_HEADERS)}",
                f"Missing: {', '.join(sec_missing) if sec_missing else 'None'}",
                f"Score: {len(sec_present)}/{len(self.SECURITY_HEADERS)}",
            ])

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data="\n".join(terminal_lines),
            )
        except Exception as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": str(e)},
                terminal_data=f"Error: {e}",
            )
