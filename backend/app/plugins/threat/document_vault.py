import logging
from app.plugins.base import OSINTPlugin, PluginResult
import httpx

logger = logging.getLogger(__name__)


class DocumentVaultPlugin(OSINTPlugin):
    plugin_id = "document-vault"
    name = "Document Vault"
    category = "threat"
    description = "Exposed documents, PDFs, config files"
    input_types = ["domain"]
    icon = "📄"

    COMMON_PATHS = [
        "/robots.txt", "/sitemap.xml", "/.env", "/.git/config",
        "/wp-config.php.bak", "/backup/", "/admin/", "/config/",
        "/.htaccess", "/crossdomain.xml", "/phpinfo.php",
    ]

    async def run(self, target: str) -> PluginResult:
        found_docs = []
        base_url = f"https://{target}"

        try:
            async with httpx.AsyncClient(timeout=5, verify=False) as client:
                for path in self.COMMON_PATHS:
                    try:
                        resp = await client.get(f"{base_url}{path}", follow_redirects=True)
                        if resp.status_code == 200:
                            found_docs.append({
                                "path": path,
                                "size": len(resp.content),
                                "type": path.split(".")[-1] if "." in path else "dir",
                                "status": resp.status_code,
                            })
                    except Exception as e:
                        logger.debug("Document check failed for %s: %s", path, e)
                        continue
        except Exception as e:
            logger.warning("Document vault scan failed for %s: %s", target, e)

        gui_data = {"Documents Found": len(found_docs), "Base URL": base_url}
        for doc in found_docs[:10]:
            gui_data[doc["path"]] = f"{doc['type'].upper()} — {doc['size']} bytes"

        terminal_lines = [f"Document Vault Scan: {base_url}", "---"]
        if found_docs:
            for doc in found_docs:
                terminal_lines.append(f"  [{doc['status']}] {doc['path']} ({doc['size']} bytes)")
        else:
            terminal_lines.append("No exposed documents found on common paths.")

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
