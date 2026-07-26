from app.plugins.base import OSINTPlugin, PluginResult
import httpx


class TechFingerprintPlugin(OSINTPlugin):
    plugin_id = "tech-fingerprint"
    name = "Tech Fingerprint"
    category = "infrastructure"
    description = "Web server, frameworks, CMS, HTTP headers"
    input_types = ["domain"]
    icon = "🖥️"

    async def run(self, target: str) -> PluginResult:
        try:
            url = f"https://{target}"
            async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as client:
                resp = await client.get(url)

            headers = resp.headers
            server = headers.get("server", "Unknown")
            powered_by = headers.get("x-powered-by", "N/A")
            ctf = headers.get("x-content-type-options", "N/A")
            frame = headers.get("x-frame-options", "N/A")
            hsts = headers.get("strict-transport-security", "N/A")
            csp = headers.get("content-security-policy", "N/A")
            set_cookie = headers.get("set-cookie", "")

            # Detect tech from headers
            techs = []
            if "php" in powered_by.lower():
                techs.append("PHP")
            if "asp.net" in (server + powered_by).lower():
                techs.append("ASP.NET")
            if "nginx" in server.lower():
                techs.append("Nginx")
            if "apache" in server.lower():
                techs.append("Apache")
            if "cloudflare" in server.lower() or "__cf" in set_cookie:
                techs.append("Cloudflare")

            gui_data = {
                "Server": server,
                "X-Powered-By": powered_by,
                "Content-Type": headers.get("content-type", "N/A"),
                "X-Frame-Options": frame,
                "X-Content-Type-Options": ctf,
                "HSTS": "Enabled" if hsts != "N/A" else "Not configured",
                "Content-Security-Policy": "Configured" if csp != "N/A" and csp else "Not configured",
                "Frameworks Detected": ", ".join(techs) if techs else "None detected",
                "Status Code": str(resp.status_code),
            }

            terminal_lines = [
                f"Server: {server}",
                f"X-Powered-By: {powered_by}",
                f"Content-Type: {headers.get('content-type', 'N/A')}",
                f"X-Frame-Options: {frame}",
                f"X-Content-Type-Options: {ctf}",
                f"HSTS: {'Enabled' if hsts != 'N/A' else 'Not configured'}",
                f"CSP: {'Configured' if csp != 'N/A' and csp else 'Not configured'}",
                f"Status: {resp.status_code}",
            ]

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
