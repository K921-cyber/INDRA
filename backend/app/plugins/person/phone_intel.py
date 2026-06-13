import logging
import re
import httpx
import phonenumbers
from phonenumbers import geocoder, carrier, phonenumberutil
from app.plugins.base import OSINTPlugin, PluginResult

logger = logging.getLogger(__name__)

class PhoneIntelPlugin(OSINTPlugin):
    plugin_id = "phone-intel"
    name = "Phone Intel"
    category = "person"
    description = "Carrier info, location, line type"
    input_types = ["phone"]
    icon = "📱"

    def _format_target(self, target: str) -> str:
        """Normalize a phone number for parsing.
        
        - Strips non-digit characters (except leading +)
        - If starts with +, use as-is
        - If exactly 10 digits (Indian mobile), prepend +91
        - Otherwise prepend + (assumes international format with country code)
        """
        cleaned = re.sub(r"[^\d+]", "", target)
        
        if not cleaned.startswith("+"):
            if len(cleaned) == 10:
                # Indian mobile number
                cleaned = f"+91{cleaned}"
            elif len(cleaned) >= 7 and len(cleaned) <= 15:
                # Likely includes a country code already
                cleaned = f"+{cleaned}"
            else:
                # Unrecognized format — keep original for the phonenumbers lib to fail gracefully
                cleaned = target.strip()
        return cleaned

    async def run(self, target: str) -> PluginResult:
        phone_str = self._format_target(target)
        
        # Default fallbacks
        parsed_number = None
        country_code_str = "Unknown"
        inferred_carrier = "Unknown"
        inferred_location = "Unknown"
        line_type = "Unknown"
        formatted_number = phone_str

        # 1. Local Offline Parsing using 'phonenumbers'
        try:
            parsed_number = phonenumbers.parse(phone_str)
            
            if phonenumbers.is_valid_number(parsed_number):
                # Get standard formatting (e.g., +91 98765 43210)
                formatted_number = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                
                # Get Country Name
                region_code = phonenumberutil.region_code_for_number(parsed_number)
                country_code_str = f"+{parsed_number.country_code} ({region_code})"
                
                # Get Location (Telecom Circle / State / City)
                geo_desc = geocoder.description_for_number(parsed_number, "en")
                if geo_desc:
                    inferred_location = geo_desc
                
                # Get Original Carrier (Pre-MNP)
                carrier_desc = carrier.name_for_number(parsed_number, "en")
                if carrier_desc:
                    inferred_carrier = carrier_desc

                # Determine Line Type
                num_type = phonenumberutil.number_type(parsed_number)
                if num_type == phonenumberutil.PhoneNumberType.MOBILE:
                    line_type = "Mobile"
                elif num_type == phonenumberutil.PhoneNumberType.FIXED_LINE:
                    line_type = "Fixed Line (Landline)"
                elif num_type == phonenumberutil.PhoneNumberType.FIXED_LINE_OR_MOBILE:
                    line_type = "Fixed Line / Mobile"
                elif num_type == phonenumberutil.PhoneNumberType.TOLL_FREE:
                    line_type = "Toll-Free"
                    
        except phonenumbers.NumberParseException as e:
            logger.debug("Local phone parsing failed for %s: %s", phone_str, e)

        # 2. Online API Enrichment (To catch post-MNP carrier changes)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Strip out formatting for the API call
                api_phone = re.sub(r"\D", "", phone_str)
                resp = await client.get(
                    f"https://api.numlookupapi.com/v1/validate/{api_phone}",
                    params={"apikey": "demo"},
                    headers={"User-Agent": "TRINETRA-OSINT/1.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Override offline data with live API data if available
                    api_carrier = data.get("carrier")
                    api_location = data.get("location")
                    api_line_type = data.get("line_type")
                    
                    if api_carrier and api_carrier != "Unknown":
                        inferred_carrier = api_carrier
                        
                    if api_location:
                        country = data.get("country_name", "")
                        inferred_location = f"{api_location}, {country}" if country else api_location
                        
                    if api_line_type and api_line_type != "Unknown":
                        line_type = api_line_type.capitalize()
                        
        except Exception as e:
            logger.debug("NumLookup API failed for %s: %s", phone_str, e)

        # 3. Compile Results
        gui_data = {
            "Phone": formatted_number,
            "Country Code": country_code_str,
            "Carrier": inferred_carrier,
            "Location": inferred_location,
            "Line Type": line_type,
        }

        terminal = f"""Phone Intel Report
═══════════════════
Phone: {formatted_number}
Country: {country_code_str}
Carrier: {inferred_carrier}
Location: {inferred_location}
Line Type: {line_type}
═══════════════════"""

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data=terminal,
        )