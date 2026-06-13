from app.plugins.base import OSINTPlugin, PluginResult
import asyncio
import re
import socket


# Regex to validate an IPv4 address
_IPV4_RE = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")


def _is_valid_ip(target: str) -> bool:
    """Check if target is a valid IPv4 address (all octets 0-255)."""
    m = _IPV4_RE.match(target)
    if not m:
        return False
    return all(0 <= int(m.group(i)) <= 255 for i in range(1, 5))


class PortScannerPlugin(OSINTPlugin):
    plugin_id = "port-scanner"
    name = "Port Scanner"
    category = "infrastructure"
    description = "Open TCP/UDP ports, service versions"
    input_types = ["domain", "ip"]
    icon = "🔌"

    # Common ports to scan
    COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995,
                    1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9090, 27017]

    SERVICE_MAP = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
        2049: "NFS", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
        5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
        9090: "HTTP-Alt", 27017: "MongoDB",
    }

    async def run(self, target: str) -> PluginResult:
        try:
            # Resolve domain to IP if target is not a valid IPv4 address
            ip = target
            if not _is_valid_ip(target):
                loop = asyncio.get_event_loop()
                ip = await loop.run_in_executor(None, lambda: socket.gethostbyname(target))

            # Scan ports concurrently
            tasks = [self._check_port(ip, port) for port in self.COMMON_PORTS]
            results = await asyncio.gather(*tasks)

            open_ports = {port: (self.SERVICE_MAP.get(port, "Unknown"), result)
                         for port, result in zip(self.COMMON_PORTS, results)
                         if result}

            gui_data = {}
            terminal_lines = [f"PORT     STATE    SERVICE", f"---"]

            for port, (service, banner) in sorted(open_ports.items()):
                gui_data[f"{port}/tcp"] = f"Open ({service})"
                terminal_lines.append(f"{port:5d}/tcp  open    {service}")

            if not open_ports:
                gui_data["Note"] = "No common ports found open or all filtered"
                terminal_lines.append("No common ports found open.")

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

    async def _check_port(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Check if a single port is open."""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
