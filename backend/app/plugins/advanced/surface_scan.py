import logging
from app.plugins.base import OSINTPlugin, PluginResult
import socket
import asyncio

logger = logging.getLogger(__name__)


class SurfaceScanPlugin(OSINTPlugin):
    plugin_id = "surface-scan"
    name = "Surface Scan"
    category = "advanced"
    description = "Aggregated risk score, attack surface analysis"
    input_types = ["domain", "ip"]
    icon = "🛡️"

    async def run(self, target: str) -> PluginResult:
        ip = target
        try:
            if not target.replace(".", "").isdigit():
                loop = asyncio.get_event_loop()
                ip = await loop.run_in_executor(None, lambda: socket.gethostbyname(target))
        except Exception as e:
            logger.debug("DNS resolution failed for %s: %s", target, e)

        # Scan a few key ports to assess exposure
        open_ports = []
        common_ports = [22, 80, 443, 8080, 8443, 3306, 3389, 5432, 6379]

        async def check_port(port: int):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=2,
                )
                writer.close()
                await writer.wait_closed()
                return port
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None

        port_results = await asyncio.gather(*[check_port(p) for p in common_ports])
        open_ports = [p for p in port_results if p is not None]

        # Assess risk based on actual findings
        risk_factors = []
        risk_score = 0

        # Open ports increase risk
        if open_ports:
            risk_score += len(open_ports) * 10
            for p in open_ports:
                risk_factors.append(f"Port {p} open")
                if p in (22, 3389):
                    risk_score += 10  # SSH/RDP exposed
                if p in (3306, 5432, 6379):
                    risk_score += 15  # Database exposed

        # IP in known govt ranges
        if ip.startswith("164.100."):
            risk_score += 20
            risk_factors.append("Government IP range")

        risk_score = min(risk_score, 100)
        risk_level = "Critical" if risk_score >= 70 else "Medium" if risk_score >= 30 else "Low"

        gui_data = {
            "Risk Score": f"{risk_score}/100",
            "Risk Level": risk_level,
            "Target": target,
            "IP": ip,
            "Open Ports": open_ports if open_ports else [],
        }

        if risk_factors:
            gui_data["Risk Factors"] = "; ".join(risk_factors)

        if risk_level == "Low":
            gui_data["Recommendation"] = "Standard monitoring — no immediate concerns"
        elif risk_level == "Medium":
            gui_data["Recommendation"] = "Review exposed services and apply security patches"
        else:
            gui_data["Recommendation"] = "Immediate review required — multiple risk factors detected"

        terminal = f"""Surface Scan Report: {target}
Risk Score:     {risk_score}/100 ({risk_level})
Target IP:      {ip}
Open Ports:     {', '.join(f'{p}/tcp' for p in open_ports) if open_ports else 'None detected'}
Factors:        {', '.join(risk_factors) if risk_factors else 'None'}
Recommendation: {gui_data['Recommendation']}"""

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data=terminal,
        )
