import logging
from app.plugins.base import OSINTPlugin, PluginResult
import asyncio

logger = logging.getLogger(__name__)


class NameServersPlugin(OSINTPlugin):
    plugin_id = "name-servers"
    name = "Name Servers"
    category = "infrastructure"
    description = "DNS records — A, AAAA, MX, NS, CNAME, TXT"
    input_types = ["domain"]
    icon = "📡"

    async def run(self, target: str) -> PluginResult:
        try:
            import dns.resolver

            loop = asyncio.get_event_loop()
            records = {}

            def resolve_type(rtype):
                try:
                    answers = dns.resolver.resolve(target, rtype, lifetime=10)
                    return [str(r) for r in answers]
                except dns.resolver.NoAnswer:
                    return []
                except dns.resolver.NXDOMAIN:
                    return []
                except dns.resolver.LifetimeTimeout:
                    return []
                except Exception:
                    return []

            for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
                records[rtype] = await loop.run_in_executor(None, lambda t=rtype: resolve_type(t))

            gui_data = {
                "A Records": records.get("A", []) or [],
                "AAAA Records": records.get("AAAA", []) or [],
                "MX Records": records.get("MX", []) or [],
                "NS Records": records.get("NS", []) or [],
                "TXT Records": records.get("TXT", []) or [],
                "CNAME": records.get("CNAME", []) or [],
            }

            # Add SOA if found
            soa = records.get("SOA", [])
            if soa:
                gui_data["SOA Record"] = soa

            # Count total records found
            total = sum(len(v) for v in records.values())
            gui_data["Total Records"] = total

            lines = [f"{target} DNS Records:"]
            for rtype, values in records.items():
                for v in values:
                    lines.append(f"  {rtype:5s}  {v}")

            if total == 0:
                lines.append("  (no DNS records found — domain may not exist or DNS query failed)")
                gui_data["Status"] = "No DNS records found"

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data="\n".join(lines),
            )
        except ImportError:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Error": "DNS resolver library not available",
                    "Status": "DNS lookup failed - missing dependency",
                },
                terminal_data=f"Error: DNS resolver library (dnspython) not installed",
            )
        except Exception as e:
            logger.warning("DNS resolution failed for %s: %s", target, e)
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Error": str(e)[:100],
                    "Status": "DNS lookup failed",
                },
                terminal_data=f"Error: DNS resolution failed for {target}\nDetails: {e}",
            )
