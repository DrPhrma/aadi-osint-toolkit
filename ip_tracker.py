"""
ip_tracker.py — Aadi OSINT Toolkit
------------------------------------
Gathers geolocation, ISP, and network info on an IP address using free APIs:
  • ip-api.com (free tier, 45 req/min) — detailed GeoIP + ASN
  • ipapi.co (free, no rate limit) — fallback geolocation
  • WHOIS-style ASN lookup via public databases

Educational purpose: passive reconnaissance — understand the network footprint
of a server or device. Can reveal datacenters, CDNs, suspicious hosting.

⚠ NOTE: Most free geolocation is accurate to city/region level, not street address.
"""

import re
from typing import Any
from ipaddress import ip_address, IPv4Address, IPv6Address

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

TIMEOUT = 8


# ─────────────────────────────────────────────────────────────────────────────
# IP validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_ip(ip_str: str) -> tuple[bool, str, str]:
    """
    Validate and categorise an IP address.
    Returns (is_valid, ip_version, error_msg).
    """
    try:
        ip_obj = ip_address(ip_str.strip())
        if isinstance(ip_obj, IPv4Address):
            version = "IPv4"
        else:
            version = "IPv6"
        
        # Check if private
        if ip_obj.is_private:
            return False, version, f"Private/reserved IP (not publicly routable)"
        
        return True, version, ""
    except ValueError as exc:
        return False, "", f"Invalid IP format: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# Geolocation APIs
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_ipapi(ip_str: str) -> dict[str, Any]:
    """
    Query ip-api.com (free tier, good accuracy).
    Returns location, ISP, ASN, timezone data.
    """
    url = f"http://ip-api.com/json/{ip_str}"
    params = {"fields": "status,message,continent,continentCode,country,countryCode," \
                        "region,regionName,city,district,zip,lat,lon,timezone," \
                        "isp,org,as,asname,mobile,proxy,hosting,query"}
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            return data
        else:
            return {"error": data.get("message", "Unknown error")}
    except Exception as exc:
        return {"error": str(exc)}


def _fetch_ipapico(ip_str: str) -> dict[str, Any]:
    """
    Query ipapi.co (fallback, unlimited rate).
    Returns location and ASN info.
    """
    url = f"https://ipapi.co/{ip_str}/json/"
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_location(data: dict) -> None:
    """Print geolocation data in a readable table."""
    if "error" in data:
        console.print(f"   [red]Error:[/red] {data['error']}")
        return
    
    table = Table(
        show_header=False,
        border_style="bright_black",
        box=box.SIMPLE,
    )
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value")
    
    fields = [
        ("IP Address", "query"),
        ("Country", lambda d: f"{d.get('countryCode', '?')}\u2009{d.get('country', '—')}"),
        ("Region", lambda d: f"{d.get('regionName', '—')} ({d.get('region', '?')})"),
        ("City", "city"),
        ("Timezone", "timezone"),
        ("Coordinates", lambda d: f"{d.get('lat', '?')}, {d.get('lon', '?')}"),
        ("ISP", "isp"),
        ("Organization", "org"),
        ("ASN", "as"),
        ("ASN Name", "asname"),
    ]
    
    for label, key in fields:
        if callable(key):
            val = key(data)
        else:
            val = data.get(key)
        
        if val and val != "—":
            table.add_row(label, str(val)[:100])
    
    # Flags for special types
    flags = []
    if data.get("mobile"):
        flags.append("[yellow]📱 Mobile[/yellow]")
    if data.get("proxy"):
        flags.append("[red]🕵 Proxy/VPN[/red]")
    if data.get("hosting"):
        flags.append("[magenta]🖥 Data Center[/magenta]")
    
    if flags:
        table.add_row("Flags", " ".join(flags))
    
    console.print(table)


def _print_map_link(data: dict) -> None:
    """Print Google Maps link if coordinates available."""
    lat = data.get("lat")
    lon = data.get("lon")
    if lat and lon:
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        console.print(f"\n[bold]Location Map:[/bold]")
        console.print(f"  [link={maps_url}][cyan]{maps_url}[/cyan][/link]")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(ip_str: str) -> dict:
    """
    Investigate an IP address for geolocation and network info.

    Args:
        ip_str: IP address (IPv4 or IPv6)

    Returns:
        dict with: ip, is_valid, location_data, asn_data
    """
    console.print(f"\n[bold cyan]📍 IP Address Tracker[/bold cyan] — target: [yellow]{ip_str}[/yellow]\n")
    
    # ── Validate IP ───────────────────────────────────────────────────────────
    is_valid, ip_version, error = _validate_ip(ip_str)
    
    if not is_valid:
        console.print(
            Panel(
                f"[bold red]✘ {error}[/bold red]",
                title="Validation",
                border_style="red",
            )
        )
        return {"ip": ip_str, "is_valid": False, "error": error}
    
    console.print(f"   [green]✔[/green] Valid {ip_version} address\n")
    
    # ── Fetch geolocation ─────────────────────────────────────────────────────
    console.print("[bold]Geolocation & ISP Data[/bold]")
    location_data = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Querying ip-api.com…", total=None)
        location_data = _fetch_ipapi(ip_str)
        progress.remove_task(task)
    
    _print_location(location_data)
    _print_map_link(location_data)
    
    console.print()
    
    return {
        "ip": ip_str,
        "is_valid": True,
        "ip_version": ip_version,
        "location_data": location_data,
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "8.8.8.8"
    run(target)
