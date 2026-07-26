import logging
from app.plugins.base import OSINTPlugin, PluginResult
import httpx
import asyncio
import socket

logger = logging.getLogger(__name__)


# Common subdomains to brute-force when API sources return empty
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "mx", "ns1", "ns2",
    "dns", "dns1", "dns2", "vpn", "remote", "gateway", "router", "firewall",
    "admin", "administrator", "portal", "login", "sso", "auth", "api", "api2",
    "dev", "staging", "stage", "test", "testing", "qa", "uat", "sandbox",
    "beta", "alpha", "demo", "preview", "canary",
    "app", "apps", "backend", "frontend", "web", "static", "cdn", "assets",
    "media", "img", "images", "images2", "upload", "uploads", "files",
    "blog", "news", "forum", "community", "support", "help", "docs", "wiki",
    "status", "monitor", "monitoring", "grafana", "kibana", "prometheus",
    "ci", "cd", "jenkins", "gitlab", "git", "github", "bitbucket", "svn",
    "db", "database", "mysql", "postgres", "redis", "mongo", "elastic",
    "search", "solr", "elastic", "cache", "memcached",
    "shop", "store", "pay", "payment", "billing", "crm", "erp",
    "panel", "cpanel", "plesk", "whm",
    "ns", "mx1", "mx2", "relay", "outlook", "exchange",
    "autodiscover", "autoconfig",
    "m", "mobile", "wap",
    "s3", "minio", "storage", "blob",
    "internal", "intranet", "private", "secure", "ssl", "tls",
    "proxy", "load", "balancer", "haproxy", "nginx", "apache",
    "log", "logs", "elk", "syslog", "ntp", "time",
    "ldap", "ad", "dc", "kdc",
    "backup", "bak", "old", "legacy", "archive",
    "mx3", "imap4", "pop3", "smtp2",
    "owa", "activesync", "autodiscover",
    "meet", "conference", "vc", "zoom", "teams",
    "kubernetes", "k8s", "docker", "registry",
    "grafana", "datadog", "newrelic", "sentry",
]


class SubdomainFinderPlugin(OSINTPlugin):
    plugin_id = "subdomain-finder"
    name = "Subdomain Finder"
    category = "infrastructure"
    description = "Discover subdomains via crt.sh, HackerTarget, and DNS brute-force"
    input_types = ["domain"]
    icon = "🔍"

    async def _query_crtsh(self, target: str, client: httpx.AsyncClient) -> set[str]:
        """Source 1: crt.sh certificate transparency logs."""
        subdomains = set()
        try:
            resp = await client.get(
                f"https://crt.sh/?q=%25.{target}&output=json",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=12,
            )
            if resp.status_code == 200:
                data = resp.json()
                for entry in data if isinstance(data, list) else []:
                    name = entry.get("name_value", "")
                    for n in name.split("\n"):
                        n = n.strip().lower()
                        if n.endswith(target) and n != target:
                            # Strip wildcard prefix
                            n = n.lstrip("*.")
                            if n.endswith(target) and n != target:
                                subdomains.add(n)
        except Exception as e:
            logger.debug("crt.sh query failed for %s: %s", target, e)
        return subdomains

    async def _query_hackertarget(self, target: str, client: httpx.AsyncClient) -> set[str]:
        """Source 2: HackerTarget host search API (plain text CSV)."""
        subdomains = set()
        try:
            resp = await client.get(
                f"https://api.hackertarget.com/hostsearch/?q={target}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    line = line.strip()
                    if "," in line:
                        hostname = line.split(",")[0].strip().lower()
                        if hostname.endswith(target) and hostname != target:
                            subdomains.add(hostname)
        except Exception as e:
            logger.debug("HackerTarget query failed for %s: %s", target, e)
        return subdomains

    async def _bruteforce_dns(self, target: str) -> set[str]:
        """Source 3: DNS brute-force common subdomain prefixes."""
        subdomains = set()

        async def _resolve(prefix: str):
            fqdn = f"{prefix}.{target}"
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, lambda: socket.getaddrinfo(fqdn, None, socket.AF_INET)
                )
                subdomains.add(fqdn)
            except (socket.gaierror, OSError):
                pass

        # Run DNS lookups in batches to avoid overwhelming the resolver
        batch_size = 20
        for i in range(0, len(COMMON_SUBDOMAINS), batch_size):
            batch = COMMON_SUBDOMAINS[i : i + batch_size]
            await asyncio.gather(*[_resolve(p) for p in batch])

        return subdomains

    async def run(self, target: str) -> PluginResult:
        # Run all three sources in parallel
        async with httpx.AsyncClient() as client:
            crtsh_task = self._query_crtsh(target, client)
            ht_task = self._query_hackertarget(target, client)
            dns_task = self._bruteforce_dns(target)

            crtsh_subs, ht_subs, dns_subs = await asyncio.gather(
                crtsh_task, ht_task, dns_task, return_exceptions=True
            )

        # Normalize results (handle exceptions from gather)
        all_subdomains: set[str] = set()
        sources_used: list[str] = []

        if isinstance(crtsh_subs, set) and crtsh_subs:
            all_subdomains.update(crtsh_subs)
            sources_used.append(f"crt.sh ({len(crtsh_subs)})")

        if isinstance(ht_subs, set) and ht_subs:
            all_subdomains.update(ht_subs)
            sources_used.append(f"HackerTarget ({len(ht_subs)})")

        if isinstance(dns_subs, set) and dns_subs:
            all_subdomains.update(dns_subs)
            sources_used.append(f"DNS brute-force ({len(dns_subs)})")

        sorted_subdomains = sorted(all_subdomains)[:100]  # Limit to 100

        # Build GUI data
        gui_data: dict = {"Subdomains Found": len(sorted_subdomains)}
        if sources_used:
            gui_data["Sources"] = ", ".join(sources_used)
        for i, sub in enumerate(sorted_subdomains[:30]):
            gui_data[sub] = "✓"

        # Build terminal data
        terminal_lines = [
            f"=== SUBDOMAIN FINDER: {target} ===",
            f"Total subdomains found: {len(sorted_subdomains)}",
        ]
        if sources_used:
            terminal_lines.append(f"Sources: {', '.join(sources_used)}")
        terminal_lines.append("")
        for sub in sorted_subdomains:
            terminal_lines.append(f"  {sub}")

        if not sorted_subdomains:
            terminal_lines.append("  (no subdomains discovered)")

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
