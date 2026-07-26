from app.plugins.base import OSINTPlugin, PluginResult


class DeepSearchPlugin(OSINTPlugin):
    plugin_id = "deep-search"
    name = "Deep Search"
    category = "advanced"
    description = "Google dorking, indexed pages, sensitive files"
    input_types = ["domain", "name"]
    icon = "🔎"

    async def run(self, target: str) -> PluginResult:
        dorks = [
            f"site:{target} filetype:pdf",
            f"site:{target} inurl:admin",
            f"site:{target} inurl:backup",
            f"site:{target} intitle:index.of",
            f"site:{target} ext:env | ext:cfg | ext:conf",
            f"site:{target} 'password' | 'login' | 'admin'",
        ]

        gui_data = {
            "Target": target,
            "Dork Queries": len(dorks),
            "Result": "Run dork queries manually (Google blocks automated dorking)",
        }

        lines = [f"Deep Search — {target}", "---"]
        for dork in dorks:
            lines.append(f"  {dork}")
        lines.extend([
            "",
            "Note: Google dorking is rate-limited.",
            "Use these queries manually in your browser:",
        ])

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(lines),
        )
