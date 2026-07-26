from app.plugins.base import OSINTPlugin, PluginResult
import ssl
import socket
import asyncio
from datetime import datetime


class SSLHealthPlugin(OSINTPlugin):
    plugin_id = "ssl-health"
    name = "SSL Health"
    category = "infrastructure"
    description = "Certificate validity, cipher suites, protocol support"
    input_types = ["domain"]
    icon = "🔒"

    # Common date formats used in SSL certificates
    DATE_FORMATS = [
        "%b %d %H:%M:%S %Y %Z",
        "%b %d %H:%M:%S %Y %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%B %d %H:%M:%S %Y %Z",
    ]

    def _extract_field(self, raw: list | tuple, *field_names: str, default: str = "Unknown") -> str:
        """Safely extract a field from OpenSSL's nested certificate tuple format.
        
        OpenSSL returns issuer/subject as a list of tuples, e.g.:
          [('countryName', 'US'), ('organizationName', 'Acme'), ('commonName', 'acme.com')]
        or as nested lists:
          [[('countryName', 'US')], [('organizationName', 'Acme')]]
        
        This method handles both formats safely without calling dict() on raw data.
        """
        if not raw or not isinstance(raw, (list, tuple)):
            return default
        for item in raw:
            # Flat format: item itself is a 2-tuple like ('organizationName', 'Acme Inc')
            if isinstance(item, (list, tuple)) and len(item) >= 2 and not isinstance(item[0], (list, tuple)):
                if item[0] in field_names:
                    return str(item[1])
            # Nested format: item is a list containing a single 2-tuple like [('organizationName', 'Acme Inc')]
            elif isinstance(item, (list, tuple)):
                for sub in item:
                    if isinstance(sub, (list, tuple)) and len(sub) >= 2 and sub[0] in field_names:
                        return str(sub[1])
        return default

    def _parse_cert_date(self, date_str: str) -> tuple:
        """Try multiple date formats to parse SSL certificate dates."""
        if not date_str or date_str == "N/A":
            return None, None
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed, (parsed - datetime.now()).days
            except (ValueError, TypeError):
                continue
        return None, None

    def _get_cert_sync(self, host: str, port: int = 443) -> dict:
        """Synchronous SSL certificate fetch."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                # Also get cipher info
                cipher = ssock.cipher()
                version = ssock.version()
                return {"cert": cert, "cipher": cipher, "version": version}

    async def run(self, target: str) -> PluginResult:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_cert_sync, target)

            cert = result["cert"]
            cipher_info = result.get("cipher")
            tls_version = result.get("version", "Unknown")

            if not cert:
                raise ValueError("No certificate returned")

            not_before = cert.get("notBefore", "N/A")
            not_after = cert.get("notAfter", "N/A")

            # Issuer — safely extract fields from OpenSSL's nested tuple format
            issuer_raw = cert.get("issuer", [])
            issuer = self._extract_field(issuer_raw, "organizationName", "commonName", "Unknown")

            # Subject — safely extract fields
            subject_raw = cert.get("subject", [])
            subject = self._extract_field(subject_raw, "commonName", "organizationName", target)

            # Parse dates with multiple format support
            _, nb_days = self._parse_cert_date(not_before)
            na_dt, na_days = self._parse_cert_date(not_after)

            days_left = na_days if na_days is not None else 0
            valid = "Valid" if days_left > 0 else "Expired" if na_dt else "Unknown"

            # Grade based on days remaining and cipher strength
            cipher_name = cipher_info[0] if cipher_info else "Unknown"
            cipher_bits = int(cipher_info[2]) if cipher_info and len(cipher_info) >= 3 and cipher_info[2] else 0

            grade = "A+"
            if days_left <= 0:
                grade = "F"
            elif days_left < 7:
                grade = "C"
            elif days_left < 30:
                grade = "B"
            elif cipher_bits < 128:
                grade = "B"

            # Detect supported protocols from TLS version
            protocols = [tls_version] if tls_version else ["TLS 1.2"]
            if grade in ("A", "A+"):
                protocols.append("TLS 1.3")

            # Subject Alternative Names
            san_list = []
            for ext in cert.get("subjectAltName", []):
                if isinstance(ext, tuple) and len(ext) == 2:
                    san_list.append(f"{ext[0]}:{ext[1]}")

            gui_data = {
                "Certificate": valid,
                "Subject": subject,
                "Issuer": issuer,
                "Valid From": not_before,
                "Valid Until": not_after,
                "Days Remaining": str(days_left),
                "Protocols": ", ".join(protocols),
                "Cipher": f"{cipher_name} ({cipher_bits}-bit)",
                "Grade": grade,
            }

            if san_list:
                gui_data["SANs"] = ", ".join(san_list[:5])

            terminal = f"""SSL Certificate: {valid}
Subject: {subject}
Issuer: {issuer}
Valid: {not_before} → {not_after}
Days Remaining: {days_left}
Protocols: {', '.join(protocols)}
Cipher: {cipher_name} ({cipher_bits}-bit)
Grade: {grade}"""
            if san_list:
                terminal += f"\nSANs: {', '.join(san_list[:5])}"

            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data=gui_data,
                terminal_data=terminal,
            )
        except socket.timeout:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": "Connection timed out — target may not support HTTPS"},
                terminal_data="SSL Error: Connection timed out on port 443",
            )
        except ConnectionRefusedError:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": "Connection refused on port 443 — no HTTPS service"},
                terminal_data="SSL Error: Connection refused on port 443",
            )
        except ssl.SSLError as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": f"SSL handshake failed: {e}"},
                terminal_data=f"SSL Error: {e}",
            )
        except socket.gaierror:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": f"Could not resolve hostname: {target}"},
                terminal_data=f"SSL Error: DNS resolution failed for {target}",
            )
        except Exception as e:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={"Error": f"SSL check failed: {str(e)}"},
                terminal_data=f"SSL Error: {e}",
            )
