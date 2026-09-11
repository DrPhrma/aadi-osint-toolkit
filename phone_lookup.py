"""
phone_lookup.py — Aadi OSINT Toolkit
--------------------------------------
Validates and extracts info from international phone numbers using:
  • phonenumbers library (Google's open-source library)
  • Public IANA carrier databases
  • Region detection and formatting

Educational purpose: understand phone number formats, detect invalid numbers,
identify carriers. Helps in OSINT when phone numbers are found in social media
profiles or leaked databases.

⚠ NOTE: This is passive validation only. We don't call or text anyone.
Real carrier lookup APIs require paid access.
"""

import re
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Try to import phonenumbers library
try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone as pn_timezone
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    console.print(
        "[yellow]⚠ phonenumbers not installed — advanced phone lookup disabled.\n"
        "   Install with: pip install phonenumbers[/yellow]"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phone number validation & parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse_phone(phone_str: str, country_hint: str = "US") -> dict[str, Any]:
    """
    Parse and validate a phone number using phonenumbers library.
    
    Args:
        phone_str: Phone number string (can include +, (), -, spaces)
        country_hint: 2-letter ISO country code (e.g., "US", "IN", "GB")
    
    Returns:
        dict with: is_valid, formatted, country_code, national_number, etc.
    """
    if not PHONENUMBERS_AVAILABLE:
        return {"error": "phonenumbers library not installed"}
    
    phone_str = phone_str.strip()
    result: dict[str, Any] = {"raw_input": phone_str}
    
    try:
        # Parse the number
        phone_obj = phonenumbers.parse(phone_str, country_hint)
        
        # Validate
        is_valid = phonenumbers.is_valid_number(phone_obj)
        is_possible = phonenumbers.is_possible_number(phone_obj)
        
        result["is_valid"] = is_valid
        result["is_possible"] = is_possible
        
        if not is_possible:
            result["error"] = "Number format is not valid"
            return result
        
        # Format variations
        result["e164"] = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
        result["international"] = phonenumbers.format_number(
            phone_obj, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        result["national"] = phonenumbers.format_number(
            phone_obj, phonenumbers.PhoneNumberFormat.NATIONAL
        )
        result["rfc3966"] = phonenumbers.format_number(
            phone_obj, phonenumbers.PhoneNumberFormat.RFC3966
        )
        
        # Extract components
        result["country_code"] = phone_obj.country_code
        result["national_number"] = phone_obj.national_number
        
        # Get country / region
        region = phonenumbers.region_code_for_number(phone_obj)
        result["country_code_iso"] = region
        
        # Get carrier (if available)
        try:
            carrier_name = carrier.name_for_number(phone_obj, "en")
            result["carrier"] = carrier_name if carrier_name else "—"
        except Exception:
            result["carrier"] = "—"
        
        # Get timezone
        try:
            tz_list = pn_timezone.time_zones_for_number(phone_obj)
            result["timezone"] = tz_list[0] if tz_list else "—"
        except Exception:
            result["timezone"] = "—"
        
        # Get geographic area
        try:
            geo = geocoder.description_for_number(phone_obj, "en")
            result["area_description"] = geo if geo else "—"
        except Exception:
            result["area_description"] = "—"
        
        # Phone type
        try:
            phone_type = phonenumbers.number_type(phone_obj)
            type_map = {
                0: "Fixed line",
                1: "Mobile",
                2: "Fixed-line or mobile",
                3: "Toll-free",
                4: "Premium rate",
                5: "Shared cost",
                6: "VoIP",
                7: "Personal",
                8: "Pager",
                9: "UAN",
                10: "Voicemail",
                11: "Unknown",
            }
            result["phone_type"] = type_map.get(phone_type, "Unknown")
        except Exception:
            result["phone_type"] = "—"
        
        return result
    
    except phonenumbers.NumberParseException as exc:
        return {"error": f"Parse error: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_validation(result: dict) -> None:
    """Print validation and formatting info."""
    if "error" in result:
        console.print(
            Panel(
                f"[bold red]✘ {result['error']}[/bold red]",
                title="Validation",
                border_style="red",
            )
        )
        return
    
    is_valid = result.get("is_valid", False)
    status = "[bold green]✔ Valid[/bold green]" if is_valid else "[bold yellow]⚠ Possible format[/bold yellow]"
    
    console.print(
        Panel(
            f"Status: {status}\n"
            f"Input: [cyan]{result['raw_input']}[/cyan]\n"
            f"E.164: [yellow]{result.get('e164', '—')}[/yellow]",
            title="Validation",
            border_style="green" if is_valid else "yellow",
        )
    )


def _print_details(result: dict) -> None:
    """Print detailed phone number info."""
    if "error" in result or not result.get("is_valid"):
        return
    
    table = Table(
        show_header=False,
        border_style="bright_black",
        box=box.SIMPLE,
    )
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value")
    
    fields = [
        ("Country Code", "country_code_iso"),
        ("Numeric CC", lambda d: f"+{d.get('country_code', '?')}"),
        ("National Number", "national_number"),
        ("Phone Type", "phone_type"),
        ("Carrier", "carrier"),
        ("Timezone", "timezone"),
        ("Geographic Area", "area_description"),
        ("National Format", "national"),
        ("International Format", "international"),
        ("RFC 3966", "rfc3966"),
    ]
    
    for label, key in fields:
        if callable(key):
            val = key(result)
        else:
            val = result.get(key)
        
        if val and val != "—":
            table.add_row(label, str(val)[:100])
    
    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(phone_str: str, country: str = "US") -> dict:
    """
    Investigate a phone number.

    Args:
        phone_str: Phone number (with or without +, (), -, spaces)
        country: ISO 2-letter country code for parsing hint (default: US)

    Returns:
        dict with: phone, is_valid, carrier, timezone, type, etc.
    """
    console.print(
        f"\n[bold cyan]📱 Phone Number Lookup[/bold cyan] — "
        f"target: [yellow]{phone_str}[/yellow]  (country hint: {country})\n"
    )
    
    if not PHONENUMBERS_AVAILABLE:
        console.print("[red]phonenumbers library not installed.[/red]")
        return {"error": "phonenumbers not available"}
    
    # ── Parse & validate ──────────────────────────────────────────────────────
    result = _parse_phone(phone_str, country)
    _print_validation(result)
    
    # ── Print details ─────────────────────────────────────────────────────────
    if result.get("is_valid"):
        console.print("\n[bold]Phone Details[/bold]")
        _print_details(result)
    
    console.print()
    
    return {
        "phone": phone_str,
        "country_hint": country,
        **result,
    }


if __name__ == "__main__":
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else "+1-202-555-0173"
    country = sys.argv[2] if len(sys.argv) > 2 else "US"
    run(phone, country)
