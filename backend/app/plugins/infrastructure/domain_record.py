
import logging
from app.plugins.base import OSINTPlugin, PluginResult
import asyncio
import socket

logger = logging.getLogger(__name__)


# Well-known WHOIS servers by TLD — avoids fragile DNS resolution
# For Indian second-level TLDs (.edu.in, .ac.in, .gov.in, .co.in, .net.in, .org.in),
# the .in server handles them all.
# Note: whois.registry.in does NOT resolve inside Docker — use whois.nixiregistry.in instead.
WHOIS_SERVERS: dict[str, str] = {
    "com": "whois.verisign-grs.com",
    "net": "whois.verisign-grs.com",
    "org": "whois.pir.org",
    "in": "whois.nixiregistry.in",
    "io": "whois.nic.io",
    "co": "whois.nic.co",
    "info": "whois.afilias.net",
    "biz": "whois.neulevel.biz",
    "gov": "whois.dotgov.gov",
    "edu": "whois.educause.edu",
    "uk": "whois.nic.uk",
    "de": "whois.denic.de",
    "ca": "whois.cira.ca",
    "au": "whois.auda.org.au",
    "jp": "whois.jprs.jp",
    "fr": "whois.nic.fr",
    "cn": "whois.cnnic.cn",
    "ru": "whois.tcinet.ru",
    "br": "whois.registro.br",
    "eu": "whois.eu",
    "xyz": "whois.nic.xyz",
    "me": "whois.nic.me",
    "tv": "whois.nic.tv",
    "app": "whois.nic.google",
    "dev": "whois.nic.google",
    "cloud": "whois.nic.cloud",
    "tech": "whois.nic.tech",
}

# Indian second-level TLDs under .in
IN_SLD_DOMAINS = {
    "ac.in", "edu.in", "gov.in", "net.in", "org.in", "co.in",
    "firm.in", "gen.in", "ind.in", "info.in", "mil.in", "name.in",
    "res.in", "biz.in", "in.net",
}


class DomainRecordPlugin(OSINTPlugin):
    plugin_id = "domain-record"
    name = "Domain Record"
    category = "infrastructure"
    description = "WHOIS registration, registrar info, creation/expiry dates"
    input_types = ["domain"]
    icon = "🌐"

    def _get_tld(self, domain: str) -> str:
        """Extract the effective TLD from a domain name.
        
        Handles second-level TLDs like .edu.in, .co.in, .gov.in, etc.
        Returns a key that matches WHOIS_SERVERS.
        """
        parts = domain.lower().strip().split(".")
        if len(parts) < 2:
            return ""
        # Check for second-level TLD (e.g., "edu.in", "co.uk")
        if len(parts) >= 3:
            sld = ".".join(parts[-2:])  # e.g., "edu.in"
            if sld in IN_SLD_DOMAINS:
                return "in"  # .in WHOIS server handles all Indian SLDs
            if sld == "co.uk":
                return "uk"
            if sld == "co.jp":
                return "jp"
            if sld == "com.au":
                return "au"
        return parts[-1]

    def _query_whois_sync(self, server: str, query: str, port: int = 43, timeout: float = 10) -> str:
        """Perform a raw WHOIS query over TCP."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((server, port))
            sock.sendall((query + "\r\n").encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            return response.decode("utf-8", errors="replace")
        finally:
            sock.close()

    def _parse_whois_field(self, raw: str, *field_names: str, default: str = "N/A") -> str:
        """Extract the first matching field from WHOIS raw text."""
        for line in raw.splitlines():
            line_lower = line.strip().lower()
            for name in field_names:
                if line_lower.lstrip().startswith(name.lower() + ":"):
                    # Extract value after the colon
                    colon_idx = line.find(":")
                    if colon_idx != -1:
                        val = line[colon_idx + 1:].strip()
                        if val:
                            return val
        return default

    def _parse_whois_dates(self, raw: str) -> tuple[str, str, str]:
        """Extract creation, expiry, and update dates from WHOIS raw text."""
        created = self._parse_whois_field(raw, "creation date", "created", "created on",
                                           "domain created", "registration date")
        expires = self._parse_whois_field(raw, "registry expiry date", "expiration date",
                                           "expiry date", "expires", "domain expires",
                                           "valid until")
        updated = self._parse_whois_field(raw, "updated date", "last updated",
                                           "modified", "changed", "last modified")
        return created, expires, updated

    def _parse_whois_name_servers(self, raw: str) -> list[str]:
        """Extract name servers from WHOIS raw text."""
        nss = []
        for line in raw.splitlines():
            ls = line.strip().lower()
            if ls.startswith("name server:") or ls.startswith("nserver:"):
                colon_idx = line.find(":")
                if colon_idx != -1:
                    val = line[colon_idx + 1:].strip()
                    if val and val not in nss:
                        nss.append(val)
        return nss

    async def run(self, target: str) -> PluginResult:
        tld = self._get_tld(target)
        whois_server = WHOIS_SERVERS.get(tld)

        if not whois_server:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Domain": target,
                    "Error": f"Unknown WHOIS server for TLD: .{tld}",
                    "Status": "WHOIS lookup not available for this TLD",
                },
                terminal_data=f"Domain: {target}\nError: No WHOIS server configured for .{tld}\nWHOIS lookup not available for this TLD",
            )

        try:
            loop = asyncio.get_event_loop()
            raw_whois = await loop.run_in_executor(
                None, self._query_whois_sync, whois_server, target
            )

            # Check for "NOT FOUND" or error responses
            if "not found" in raw_whois.lower() or "no data found" in raw_whois.lower():
                return PluginResult(
                    plugin_id=self.plugin_id,
                    plugin_name=self.name,
                    category=self.category,
                    target=target,
                    gui_data={
                        "Domain": target,
                        "Status": "Domain not found in WHOIS database",
                        "WHOIS Server": whois_server,
                    },
                    terminal_data=f"Domain: {target}\nStatus: Domain not found in WHOIS database\nWHOIS Server: {whois_server}",
                )

            registrar = self._parse_whois_field(raw_whois, "registrar", "registrar name",
                                                 "registrar:", "sponsoring registrar")
            created, expires, updated = self._parse_whois_dates(raw_whois)
            name_servers = self._parse_whois_name_servers(raw_whois)
            status = self._parse_whois_field(raw_whois, "domain status", "status")
            registrant = self._parse_whois_field(raw_whois, "registrant", "registrant name",
                                                  "org", "organization", "organization name")
            emails = self._parse_whois_field(raw_whois, "registrant email", "admin email",
                                              "tech email", "e-mail")
            emails_list = [e.strip() for e in emails.split(",")] if emails and emails != "N/A" else []

            gui_data = {
                "Domain": target,
                "Registrar": registrar,
                "Created": created,
                "Expires": expires,
                "Updated": updated,
                "Name Servers": name_servers if name_servers else [],
                "Status": status,
                "Registrant": registrant,
                "Emails": emails_list,
                "WHOIS Server": whois_server,
            }

            terminal_lines = [
                f"Domain Name: {target}",
                f"Registrar: {registrar}",
                f"Created: {created}",
                f"Expires: {expires}",
                f"Updated: {updated}",
                f"Name Servers: {', '.join(name_servers) if name_servers else 'N/A'}",
                f"Registrant: {registrant}",
                f"Emails: {', '.join(emails_list) if emails_list else 'N/A'}",
                f"WHOIS Server: {whois_server}",
            ]

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data="\n".join(terminal_lines),
            )

        except socket.timeout:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Domain": target,
                    "Error": f"WHOIS connection to {whois_server} timed out",
                    "Status": "WHOIS lookup failed - timeout",
                },
                terminal_data=f"Domain: {target}\nError: WHOIS connection to {whois_server} timed out",
            )
        except socket.gaierror as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Domain": target,
                    "Error": f"Cannot resolve WHOIS server: {whois_server}",
                    "Status": "WHOIS lookup failed - DNS resolution error",
                },
                terminal_data=f"Domain: {target}\nError: Cannot resolve WHOIS server {whois_server}\nDNS error: {e}",
            )
        except ConnectionRefusedError:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Domain": target,
                    "Error": f"Connection refused by WHOIS server: {whois_server}",
                    "Status": "WHOIS lookup failed - connection refused",
                },
                terminal_data=f"Domain: {target}\nError: Connection refused by WHOIS server {whois_server}",
            )
        except Exception as e:
            logger.debug("WHOIS lookup failed for %s: %s", target, e)
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Domain": target,
                    "Error": f"WHOIS lookup error: {str(e)[:100]}",
                    "Status": "WHOIS lookup failed",
                },
                terminal_data=f"Domain: {target}\nError: WHOIS lookup failed\nDetails: {e}",
            )
