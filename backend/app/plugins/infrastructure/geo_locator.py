from app.plugins.base import OSINTPlugin, PluginResult
import asyncio


class GeoLocatorPlugin(OSINTPlugin):
    plugin_id = "geo-locator"
    name = "Geo Locator"
    category = "infrastructure"
    description = "Server location, ISP, ASN info"
    input_types = ["domain", "ip"]
    icon = "📍"

    async def run(self, target: str) -> PluginResult:
        try:
            # Resolve domain to IP first if needed
            ip = target
            if not target.replace(".", "").isdigit():
                import socket
                loop = asyncio.get_event_loop()
                ip = (await loop.run_in_executor(None, lambda: socket.gethostbyname(target)))

            # Use ip-api.com for geo lookup (free, no key needed)
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"http://ip-api.com/json/{ip}")
                data = resp.json()

            if data.get("status") == "success":
                gui_data = {
                    "IP": ip,
                    "Country": data.get("country", "Unknown"),
                    "Region": data.get("regionName", ""),
                    "City": data.get("city", ""),
                    "ISP": data.get("isp", "Unknown"),
                    "ASN": f"AS{data.get('as', '').split()[0]}" if data.get("as") else "N/A",
                    "Latitude": str(data.get("lat", "")),
                    "Longitude": str(data.get("lon", "")),
                    "Timezone": data.get("timezone", ""),
                }
                terminal = f"""IP: {ip}
Country: {data.get('country', 'Unknown')}
City: {data.get('city', 'Unknown')}
ISP: {data.get('isp', 'Unknown')}
ASN: AS{data.get('as', '').split()[0] if data.get('as') else 'N/A'}
Lat: {data.get('lat', '')}
Lon: {data.get('lon', '')}"""
            else:
                gui_data = {"IP": ip, "Error": "GeoIP lookup failed"}
                terminal = f"IP: {ip}\nGeoIP lookup failed"

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data=terminal,
            )
        except Exception as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"IP": target, "Error": str(e)},
                terminal_data=f"Error: {e}",
            )
