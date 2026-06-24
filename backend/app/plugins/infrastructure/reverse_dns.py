import asyncio
from app.plugins.base import OSINTPlugin, PluginResult


class ReverseDNSPlugin(OSINTPlugin):
    plugin_id = "reverse-dns"
    name = "Reverse DNS"
    category = "infrastructure"
    description = "Resolves target to IP and fetches PTR records"
    # Updated to support both domains and IPs as input
    input_types = ["domain", "ip"]
    icon = "🔄"

    async def run(self, target: str) -> PluginResult:
        # Initialize default return structures
        gui_data = {
            "Target": target,
            "Resolved IP": "N/A",
            "PTR Records": "None found",
        }
        terminal = f"Target: {target}\n"

        try:
            # Inline imports to avoid global dependency overhead if required by your framework
            import socket
            import dns.reversename
            import dns.resolver

            loop = asyncio.get_running_loop()

            # Step 1: Resolve target to IP if it's a domain. 
            # If it's already an IP, gethostbyname will just return it.
            resolved_ip = await loop.run_in_executor(
                None, lambda: socket.gethostbyname(target)
            )
            gui_data["Resolved IP"] = resolved_ip

            # Step 2: Perform the Reverse DNS lookup asynchronously using dnspython
            def do_ptr_lookup(ip_addr):
                rev_name = dns.reversename.from_address(ip_addr)
                # Using a default lifetime timeout of 5 seconds, adjust as needed
                answers = dns.resolver.resolve(rev_name, "PTR", lifetime=5)
                return [str(a) for a in answers]

            ptr_records = await loop.run_in_executor(None, do_ptr_lookup, resolved_ip)

            # Step 3: Format the successful results
            ptr_string = ", ".join(ptr_records) if ptr_records else "None"
            gui_data["PTR Records"] = ptr_string

            terminal += f"Resolved IP: {resolved_ip}\nPTR Records: {ptr_string}"

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data=terminal,
            )

        except Exception as e:
            # Handle failures gracefully within the framework's structure
            gui_data["PTR Records"] = "Error / Not found"
            terminal += f"Error: {str(e)}"
            
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data=terminal,
            )
