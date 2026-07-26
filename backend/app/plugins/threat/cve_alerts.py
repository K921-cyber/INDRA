import logging
from app.plugins.base import OSINTPlugin, PluginResult
import httpx

logger = logging.getLogger(__name__)


class CVEAlertsPlugin(OSINTPlugin):
    plugin_id = "cve-alerts"
    name = "CVE Alerts"
    category = "threat"
    description = "Vulnerabilities matching your tech stack (from NVD)"
    input_types = ["domain", "ip"]
    icon = "⚠️"

    async def run(self, target: str) -> PluginResult:
        cves = []

        # Try to fetch from NVD API using the target as keyword
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={target}&resultsPerPage=10",
                    headers={"User-Agent": "TRINETRA-OSINT/1.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for vuln in data.get("vulnerabilities", []):
                        cve = vuln.get("cve", {})
                        cve_id = cve.get("id", "Unknown")
                        metrics = cve.get("metrics", {})
                        # Try CVSS v3.1 first, then v3.0, then v2.0
                        score = "N/A"
                        severity = "Unknown"
                        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                            metric = metrics.get(version)
                            if metric and len(metric) > 0:
                                cvss_data = metric[0].get("cvssData", {})
                                score = cvss_data.get("baseScore", "N/A")
                                severity = cvss_data.get("baseSeverity", "Unknown")
                                break
                        description = ""
                        for desc in cve.get("descriptions", []):
                            if desc.get("lang") == "en":
                                description = desc.get("value", "")[:150]
                                break
                        cves.append({
                            "id": cve_id,
                            "score": str(score),
                            "severity": severity,
                            "description": description,
                        })
        except Exception as e:
            logger.debug("NVD API request failed for %s: %s", target, e)

        if not cves:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "CVE Count": 0,
                    "Target": target,
                    "Status": "No CVEs found matching this target",
                    "Note": "Search the NVD database directly at https://nvd.nist.gov/ for comprehensive results",
                },
                terminal_data=f"CVE Vulnerability Report for: {target}\n---\nNo CVEs found matching this target.\nSearch the NVD database directly at https://nvd.nist.gov/",
            )

        gui_data = {"CVE Count": len(cves)}
        for cve in cves[:10]:
            label = f"{cve['score']} {cve['severity']}" if cve['severity'] != 'Unknown' else cve['score']
            gui_data[cve["id"]] = f"{label} — {cve['description'][:100]}"

        terminal_lines = [f"CVE Vulnerability Report for: {target}", "---"]
        for cve in cves[:10]:
            label = f"{cve['score']} {cve['severity']}" if cve['severity'] != 'Unknown' else cve['score']
            terminal_lines.append(f"{cve['id']} ({label})")
            if cve['description']:
                terminal_lines.append(f"  {cve['description'][:120]}")

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
