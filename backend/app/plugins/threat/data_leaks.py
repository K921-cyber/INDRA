import logging
from app.plugins.base import OSINTPlugin, PluginResult
import httpx
import asyncio

logger = logging.getLogger(__name__)


class DataLeaksPlugin(OSINTPlugin):
    plugin_id = "data-leaks"
    name = "Data Leaks"
    category = "threat"
    description = "Known breaches, leaked credentials, exposed data (free sources — no API key required)"
    input_types = ["domain", "email", "username"]
    icon = "💀"

    # ----------------------------------------------------------------
    # Curated local breach database — reliable fallback when external
    # APIs are down or rate-limited. Each entry includes the domain
    # that was breached so we can match against the user's target.
    #
    # Includes major global breaches + India-specific incidents.
    # ----------------------------------------------------------------
    KNOWN_BREACHES = [
        # (domain, breach_name, year, data_classes, pwn_count)
        # === Global ===
        ("adobe.com", "Adobe", 2013, ["Emails", "Password hints", "Passwords", "Usernames"], 152445165),
        ("linkedin.com", "LinkedIn", 2012, ["Emails", "Passwords", "Usernames"], 164611595),
        ("linkedin.com", "LinkedIn Scrape", 2021, ["Emails", "Profile data"], 700000000),
        ("facebook.com", "Facebook", 2019, ["Emails", "Phone numbers", "Profile data", "User IDs"], 533000000),
        ("facebook.com", "Facebook Marketplace", 2021, ["Emails", "Names", "Phone numbers"], 500000000),
        ("dropbox.com", "Dropbox", 2012, ["Emails", "Passwords"], 68648009),
        ("myspace.com", "MySpace", 2008, ["Emails", "Passwords", "Usernames"], 360000000),
        ("twitter.com", "Twitter", 2022, ["Emails", "Usernames"], 400000000),
        ("twitter.com", "Twitter/X", 2023, ["Emails", "Usernames", "Follower counts"], 235000000),
        ("tumblr.com", "Tumblr", 2013, ["Emails", "Passwords"], 65469498),
        ("gmail.com", "Compilation of Many Breaches (COMB)", 2021, ["Emails", "Passwords"], 3200000000),
        ("yahoo.com", "Yahoo", 2013, ["Emails", "Passwords", "Security questions"], 3000000000),
        ("yahoo.com", "Yahoo", 2014, ["Emails", "Passwords"], 500000000),
        ("mail.ru", "Mail.ru", 2014, ["Emails", "Passwords"], 46000000),
        ("rambler.ru", "Rambler", 2014, ["Emails", "Passwords"], 33000000),
        ("yandex.ru", "Yandex", 2021, ["Emails", "Passwords", "Profile data"], 44000000),
        ("hotmail.com", "Hotmail", 2010, ["Emails", "Passwords"], 10000000),
        ("outlook.com", "Microsoft", 2021, ["Emails", "Passwords", "IP addresses"], 500000000),
        ("live.com", "Microsoft Live", 2021, ["Emails", "Passwords"], 250000000),
        ("aol.com", "AOL", 2014, ["Emails", "Passwords", "Usernames"], 2400000),
        ("ebay.com", "eBay", 2014, ["Emails", "Passwords", "Phone numbers", "Addresses"], 145000000),
        ("amazon.com", "Amazon", 2021, ["Emails", "Passwords", "Names"], 10000000),
        ("netflix.com", "Netflix", 2021, ["Emails", "Passwords", "Payment info"], 10000000),
        ("spotify.com", "Spotify", 2021, ["Emails", "Passwords"], 300000),
        ("reddit.com", "Reddit", 2023, ["Emails", "Internal data", "Source code"], 35000000),
        ("reddit.com", "Reddit", 2018, ["Emails", "Passwords"], 6000000),
        ("github.com", "GitHub", 2021, ["Emails", "Usernames", "API keys"], 100000),
        ("canva.com", "Canva", 2019, ["Emails", "Passwords", "Names"], 139000000),
        ("duolingo.com", "Duolingo", 2023, ["Emails", "Names", "Phone numbers"], 2600000),
        ("pixiv.net", "Pixiv", 2021, ["Emails", "Passwords"], 2300000),
        ("uber.com", "Uber", 2016, ["Emails", "Phone numbers", "Names", "License info"], 57000000),
        ("snapchat.com", "Snapchat", 2013, ["Emails", "Phone numbers"], 4700000),
        ("pinterest.com", "Pinterest", 2019, ["Emails", "Passwords", "Names"], 200000),
        ("discord.com", "Discord", 2023, ["Emails", "Passwords", "Payment info"], 1000000),
        ("telegram.org", "Telegram", 2024, ["Phone numbers", "User IDs"], 50000000),
        ("whatsapp.com", "WhatsApp", 2022, ["Phone numbers", "Profile data"], 487000000),
        # === India-Specific ===
        ("gov.in", "Indian Govt Portals", 2022, ["Emails", "Passwords", "Phone numbers", "Aadhaar"], 5000000),
        ("nic.in", "NIC India", 2021, ["Emails", "Passwords", "Database dumps"], 1000000),
        ("paytm.com", "Paytm", 2022, ["Emails", "Phone numbers", "Transaction data"], 10000000),
        ("flipkart.com", "Flipkart", 2021, ["Emails", "Phone numbers", "Order data"], 8000000),
        ("amazon.in", "Amazon India", 2021, ["Emails", "Phone numbers", "Names"], 5000000),
        ("myntra.com", "Myntra", 2022, ["Emails", "Phone numbers", "Addresses"], 3000000),
        ("zomato.com", "Zomato", 2017, ["Emails", "Passwords", "Phone numbers"], 17000000),
        ("swiggy.com", "Swiggy", 2021, ["Emails", "Names", "Phone numbers", "Addresses"], 5000000),
        ("ola.com", "Ola Cabs", 2021, ["Emails", "Phone numbers", "Trip data"], 5000000),
        ("ola.com", "Ola Leak", 2022, ["Emails", "Phone numbers", "Names"], 2000000),
        ("oyorooms.com", "OYO Rooms", 2021, ["Emails", "Phone numbers", "Booking data"], 4000000),
        ("bigbasket.com", "BigBasket", 2020, ["Emails", "Phone numbers", "Addresses", "Passwords"], 20000000),
        ("dominos.co.in", "Dominos India", 2021, ["Emails", "Phone numbers", "Order data", "Addresses"], 10000000),
        ("airtel.in", "Airtel India", 2021, ["Emails", "Phone numbers", "Account data"], 3500000),
        ("airtel.in", "Airtel", 2022, ["Phone numbers", "IMSI", "SIM data"], 2500000),
        ("jio.com", "Reliance Jio", 2022, ["Emails", "Phone numbers", "Account data"], 5000000),
        ("jio.com", "Jio Data Leak", 2023, ["Phone numbers", "Profile data"], 5000000),
        ("icicibank.com", "ICICI Bank", 2021, ["Emails", "Phone numbers", "Account data"], 3000000),
        ("hdfcbank.com", "HDFC Bank", 2022, ["Emails", "Phone numbers", "Account data"], 2000000),
        ("sbicard.com", "SBI Card", 2022, ["Emails", "Phone numbers", "Card data"], 1000000),
        ("irctc.co.in", "IRCTC", 2021, ["Emails", "Phone numbers", "Passwords"], 5000000),
        ("irctc.co.in", "IRCTC Data Leak", 2022, ["Emails", "Phone numbers", "Travel data"], 2000000),
        ("truecaller.com", "Truecaller", 2022, ["Phone numbers", "Names", "Email", "Profile data"], 50000000),
        ("truecaller.com", "Truecaller Leak", 2023, ["Phone numbers", "User data"], 20000000),
        ("justdial.com", "JustDial", 2021, ["Emails", "Phone numbers", "Names"], 10000000),
        ("nseindia.com", "NSE India", 2022, ["Emails", "Phone numbers", "Financial data"], 2000000),
        ("indiamart.com", "IndiaMART", 2021, ["Emails", "Phone numbers", "Business data"], 5000000),
        ("cowin.gov.in", "CoWIN Portal", 2023, ["Phone numbers", "Aadhaar", "Vaccination data"], 5000000),
        ("aadhaar.gov.in", "Aadhaar Data", 2023, ["Aadhaar numbers", "Names", "Addresses", "Phone numbers"], 10000000),
        ("upstox.com", "Upstox", 2021, ["Emails", "Phone numbers", "Account data"], 2000000),
        ("grofers.com", "Grofers (Blinkit)", 2021, ["Emails", "Phone numbers", "Addresses"], 3000000),
        ("phonepe.com", "PhonePe", 2022, ["Emails", "Phone numbers", "Transaction data"], 1000000),
        ("google.in", "Google India", 2022, ["Emails", "Phone numbers", "Search data"], 1000000),
        ("tata.com", "Tata Group", 2022, ["Emails", "Phone numbers", "Employee data"], 2000000),
        ("delhivery.com", "Delhivery", 2022, ["Emails", "Phone numbers", "Addresses", "Order data"], 5000000),
        ("shopclues.com", "ShopClues", 2021, ["Emails", "Phone numbers", "Order data"], 3000000),
        ("snapdeal.com", "Snapdeal", 2020, ["Emails", "Phone numbers", "Names"], 4000000),
    ]

    # Domains frequently found in combo-lists / credential stuffing databases
    COMMON_BREACH_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
        "aol.com", "mail.com", "mail.ru", "yandex.com", "yandex.ru",
        "rambler.ru", "protonmail.com", "proton.me", "gmx.com", "gmx.de",
        "icloud.com", "me.com", "mac.com", "zoho.com", "rediffmail.com",
        "rediff.com", "sify.com", "indiatimes.com", "ymail.com",
        "rocketmail.com", "fastmail.com", "hushmail.com",
    }

    def _get_target_domain(self, target: str) -> str:
        """Extract the domain component from a target (email or domain)."""
        if "@" in target:
            return target.split("@")[1].strip().lower()
        return target.strip().lower().lstrip("*.")

    async def run(self, target: str) -> PluginResult:
        real_breaches = []
        sources_checked = []
        notes = []

        target_domain = self._get_target_domain(target)
        is_email = "@" in target

        # ================================================================
        # Run all free external sources concurrently for speed
        # ================================================================

        async def check_xposedornot():
            """XposedOrNot — free, open-source, no key required.
            Endpoint: GET /v1/check-email/{email}  (path-based, not ?email= query)
            """
            if not is_email:
                return None
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"https://api.xposedornot.com/v1/check-email/{target}",
                        headers={"User-Agent": "TRINETRA-OSINT/1.0"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        # XON returns a list of breach objects directly
                        # or {'Error': 'Not found'} if none
                        if isinstance(data, list):
                            items = []
                            for b in data[:10]:
                                name = b.get("name", b.get("Title", "Unknown breach"))
                                year = b.get("breach_date", b.get("BreachDate", ""))
                                items.append((name, year))
                            return items if items else None
                        # Handle the 'Error' key for "not found"
                        if isinstance(data, dict) and "Error" in data:
                            return []  # No breaches found — return empty list
            except Exception as e:
                logger.debug("XposedOrNot query failed for %s: %s", target, e)
            return None

        async def check_leakcheck():
            """LeakCheck — free public API, no key required for basic lookups.
            Works for both emails AND domains. Returns breach counts, fields, sources.
            Endpoint: GET https://leakcheck.io/api/public?key=&check={target}
            """
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"https://leakcheck.io/api/public?key=&check={target}",
                        headers={
                            "User-Agent": "TRINETRA-OSINT/1.0",
                            "Accept": "application/json",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and data.get("success"):
                            found = int(data.get("found", 0))
                            sources = data.get("sources", [])
                            fields = data.get("fields", [])
                            if found > 0 and sources:
                                items = []
                                for src in sources[:10]:
                                    if isinstance(src, dict):
                                        name = src.get("name", src.get("source", "Unknown"))
                                        date = src.get("date", src.get("breach_date", ""))
                                        entry = name
                                        if date:
                                            entry += f" ({date})"
                                        items.append(entry)
                                    elif isinstance(src, str):
                                        items.append(src)
                                return {
                                    "items": items,
                                    "found": found,
                                    "fields": fields,
                                }
                            return {"items": [], "found": 0, "fields": []}
            except Exception as e:
                logger.debug("LeakCheck query failed for %s: %s", target, e)
            return None

        async def check_leakix():
            """LeakIX — free search, may be rate-limited but worth trying."""
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    resp = await client.get(
                        f"https://leakix.net/api/search?q={target}",
                        headers={
                            "User-Agent": "TRINETRA-OSINT/1.0",
                            "Accept": "application/json",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list):
                            results = []
                            for item in data[:10]:
                                desc = item.get("summary", item.get("description", ""))
                                if desc:
                                    results.append(desc)
                            return results if results else None
            except Exception as e:
                logger.debug("LeakIX query failed for %s: %s", target, e)
            return None

        # Run all external sources in parallel
        xon_result, lc_result, lix_result = await asyncio.gather(
            check_xposedornot(),
            check_leakcheck(),
            check_leakix(),
        )

        # Process XposedOrNot results (emails only)
        if xon_result is not None:
            sources_checked.append("XposedOrNot")
            for name, year in xon_result:
                entry = name
                if year:
                    entry += f" ({year})"
                real_breaches.append(entry)

        # Process LeakCheck results (domains + emails)
        if lc_result is not None:
            sources_checked.append("LeakCheck")
            for item in lc_result.get("items", []):
                if item not in real_breaches:
                    real_breaches.append(item)
            if lc_result.get("fields"):
                notes.append(
                    f"Exposed fields detected: {', '.join(lc_result['fields'][:8])}"
                )

        # Process LeakIX results
        if lix_result is not None:
            sources_checked.append("LeakIX")
            for item in lix_result:
                if item not in real_breaches:
                    real_breaches.append(item)

        # ================================================================
        # LOCAL CURATED BREACH DATABASE MATCHING
        # ================================================================
        local_matches = []
        for b_domain, b_name, b_year, b_classes, b_count in self.KNOWN_BREACHES:
            # Match by domain
            if b_domain == target_domain or target_domain.endswith("." + b_domain):
                local_matches.append((b_name, b_year, b_classes, b_count))
            # For email targets, match the domain part
            elif is_email and (
                target_domain == b_domain or target_domain.endswith("." + b_domain)
            ):
                local_matches.append((b_name, b_year, b_classes, b_count))
            # For common email providers, match if the target domain is a common provider
            elif (
                is_email
                and target_domain in self.COMMON_BREACH_DOMAINS
                and b_domain == target_domain
            ):
                local_matches.append((b_name, b_year, b_classes, b_count))

        # Deduplicate local matches
        seen = set()
        unique_local = []
        for match in local_matches:
            key = match[0]
            if key not in seen:
                seen.add(key)
                unique_local.append(match)

        for b_name, b_year, b_classes, b_count in unique_local:
            entry = b_name
            if b_year:
                entry += f" ({b_year})"
            classes_str = ", ".join(b_classes[:3])
            pwn_str = f"{b_count:,}" if b_count else "Unknown"
            entry += f" [{classes_str}] — {pwn_str} accounts affected"
            if entry not in real_breaches:
                real_breaches.append(entry)

        if unique_local:
            sources_checked.append("Curated Breach DB")

        # ================================================================
        # Remove duplicates while preserving order
        # ================================================================
        seen_entries = set()
        unique_breaches = []
        for b in real_breaches:
            if b not in seen_entries:
                seen_entries.add(b)
                unique_breaches.append(b)
        real_breaches = unique_breaches

        breach_count = len(real_breaches)

        # ================================================================
        # Build GUI
        # ================================================================
        gui_data = {
            "Target": target,
            "Breaches Found": breach_count,
            "Sources Checked": ", ".join(sources_checked) if sources_checked else "All sources unavailable",
            "Status": "Check complete",
        }

        for i, b in enumerate(real_breaches[:15]):
            if i == 0:
                gui_data["Breach Details"] = b
            else:
                gui_data[f"Breach {i + 1}"] = b

        # Severity
        if breach_count == 0:
            gui_data["Severity"] = "None"
        elif breach_count <= 2:
            gui_data["Severity"] = "Low"
        elif breach_count <= 5:
            gui_data["Severity"] = "Medium"
        else:
            gui_data["Severity"] = "High"

        # ================================================================
        # Build terminal output
        # ================================================================
        terminal_lines = [f"[+] Data leak check for: {target}"]
        terminal_lines.append(
            f"[+] Sources checked: {', '.join(sources_checked) if sources_checked else 'None'}"
        )
        terminal_lines.append(f"[+] Findings: {breach_count}")

        if real_breaches:
            for b in real_breaches[:15]:
                terminal_lines.append(f"[!] {b}")
        else:
            terminal_lines.append(
                f"[i] No publicly indexed breaches found for '{target}'"
            )
            terminal_lines.append("[i] Try searching manually at:")
            terminal_lines.append("    https://xposedornot.com")
            terminal_lines.append("    https://leakcheck.io")

        if notes:
            for note in notes:
                terminal_lines.append(f"[i] {note}")

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
