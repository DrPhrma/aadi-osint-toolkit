"""
domain_intel.py — Aadi OSINT Toolkit
--------------------------------------
Gathers passive domain intelligence using only public, legal data sources:
  • DNS records (A, MX, TXT, NS, CNAME) via dnspython
  • SSL/TLS certificate details via the built-in ssl module
  • WHOIS data via the python-whois library (if available)

Educational purpose: passive reconnaissance of a domain's public footprint —
no exploitation, no brute-forcing, no zone-transfer attacks.
"""

import socket
import ssl
import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# ── Optional imports (gracefully degraded if not installed) ───────────────────
try:
    import dns.resolver as dns_resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    console.print("[yellow]⚠  dnspython not installed — DNS lookups disabled.[/yellow]")

try:
    import whois as whois_lib
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# DNS helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve(domain: str, record_type: str) -> list[str]:
    """Resolve a single DNS record type; return list of string answers."""
    if not DNS_AVAILABLE:
        return []
    try:
        answers = dns_resolver.resolve(domain, record_type, lifetime=8)
        return [str(r) for r in answers]
    except (dns_resolver.NoAnswer, dns_resolver.NXDOMAIN, dns_resolver.NoNameservers):
        return []
    except Exception as exc:
        return [f"Error: {exc}"]


def fetch_dns_records(domain: str) -> dict[str, list[str]]:
    """Return a mapping of record type → list of values."""
    record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]
    records: dict[str, list[str]] = {}
    for rtype in record_types:
        answers = _resolve(domain, rtype)
        if answers:
            records[rtype] = answers
    return records


# ─────────────────────────────────────────────────────────────────────────────
# SSL helpers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_ssl_info(domain: str, port: int = 443) -> dict[str, Any]:
    """
    Connect to domain:port with TLS and pull certificate fields.
    Returns a dict of certificate metadata (or an error message).
    """
    result: dict[str, Any] = {}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=8) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=domain) as tls_sock:
                cert = tls_sock.getpeercert()
                cipher = tls_sock.cipher()

        # Subject / Issuer
        def _dict_from_rdns(rdns):
            out = {}
            for pair in rdns:
                for key, val in pair:
                    out[key] = val
            return out

        result["subject"] = _dict_from_rdns(cert.get("subject", ()))
        result["issuer"] = _dict_from_rdns(cert.get("issuer", ()))
        result["version"] = cert.get("version")

        # Validity dates
        not_before_raw = cert.get("notBefore", "")
        not_after_raw = cert.get("notAfter", "")

        def _parse_ssl_date(s: str) -> str:
            try:
                dt = datetime.datetime.strptime(s, "%b %d %H:%M:%S %Y %Z")
                return dt.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                return s

        result["not_before"] = _parse_ssl_date(not_before_raw)
        result["not_after"] = _parse_ssl_date(not_after_raw)

        # Days until expiry
        try:
            expiry_dt = datetime.datetime.strptime(not_after_raw, "%b %d %H:%M:%S %Y %Z")
            delta = expiry_dt - datetime.datetime.utcnow()
            result["days_until_expiry"] = delta.days
        except ValueError:
            result["days_until_expiry"] = None

        # SANs (Subject Alternative Names)
        sans: list[str] = []
        for entry_type, value in cert.get("subjectAltName", []):
            if entry_type == "DNS":
                sans.append(value)
        result["subject_alt_names"] = sans

        # Cipher suite
        if cipher:
            result["cipher_name"] = cipher[0]
            result["tls_version"] = cipher[1]
            result["cipher_bits"] = cipher[2]

        result["error"] = None

    except ssl.SSLCertVerificationError as exc:
        result["error"] = f"SSL verification failed: {exc}"
    except ConnectionRefusedError:
        result["error"] = f"Port {port} refused — no HTTPS service?"
    except socket.timeout:
        result["error"] = "Connection timed out"
    except OSError as exc:
        result["error"] = str(exc)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# WHOIS helper
# ─────────────────────────────────────────────────────────────────────────────

def fetch_whois(domain: str) -> dict[str, Any]:
    """Retrieve WHOIS registration data (requires python-whois)."""
    if not WHOIS_AVAILABLE:
        return {"error": "python-whois not installed (pip install python-whois)"}
    try:
        w = whois_lib.whois(domain)
        raw: dict[str, Any] = {}

        def _fmt(val):
            if isinstance(val, list):
                return [str(v) for v in val]
            return str(val) if val is not None else None

        for key in ("registrar", "creation_date", "expiration_date",
                    "updated_date", "name_servers", "status",
                    "emails", "country", "org"):
            raw[key] = _fmt(getattr(w, key, None))
        return raw
    except Exception as exc:
        return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_dns(records: dict[str, list[str]]) -> None:
    if not records:
        console.print("   [dim]No DNS records retrieved.[/dim]")
        return
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
    )
    table.add_column("Type", style="cyan", width=8)
    table.add_column("Value")
    for rtype, values in records.items():
        for i, val in enumerate(values):
            table.add_row(rtype if i == 0 else "", val)
    console.print(table)


def _print_ssl(ssl_info: dict) -> None:
    if ssl_info.get("error"):
        console.print(f"   [red]SSL Error:[/red] {ssl_info['error']}")
        return

    expiry_days = ssl_info.get("days_until_expiry")
    expiry_color = "green" if expiry_days and expiry_days > 30 else "red"

    panel_lines = []
    subj = ssl_info.get("subject", {})
    issuer = ssl_info.get("issuer", {})
    panel_lines.append(f"[bold]Subject CN[/bold]   : {subj.get('commonName', '—')}")
    panel_lines.append(f"[bold]Issuer   [/bold]    : {issuer.get('organizationName', '—')}")
    panel_lines.append(f"[bold]Valid From[/bold]   : {ssl_info.get('not_before', '—')}")
    panel_lines.append(f"[bold]Valid Until[/bold]  : {ssl_info.get('not_after', '—')}  "
                       f"([{expiry_color}]{expiry_days} days left[/{expiry_color}])")
    panel_lines.append(f"[bold]TLS Version[/bold]  : {ssl_info.get('tls_version', '—')}")
    panel_lines.append(f"[bold]Cipher     [/bold]  : {ssl_info.get('cipher_name', '—')} "
                       f"({ssl_info.get('cipher_bits', '?')} bit)")
    sans = ssl_info.get("subject_alt_names", [])
    if sans:
        panel_lines.append(f"[bold]SANs ({len(sans)})[/bold]     : {', '.join(sans[:6])}"
                           + (" …" if len(sans) > 6 else ""))

    console.print(Panel("\n".join(panel_lines), title="SSL Certificate", border_style="cyan"))


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(domain: str) -> dict:
    """
    Gather and display domain intelligence.

    Returns:
        dict with keys: domain, dns_records, ssl_info, whois_info
    """
    # Sanitise input: strip protocol, trailing slashes, whitespace
    domain = domain.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0]

    console.print(f"\n[bold cyan]🌐 Domain Intelligence[/bold cyan] — target: [yellow]{domain}[/yellow]\n")

    # ── DNS ───────────────────────────────────────────────────────────────────
    console.print("[bold]DNS Records[/bold]")
    dns_records = fetch_dns_records(domain)
    _print_dns(dns_records)

    # ── SSL ───────────────────────────────────────────────────────────────────
    console.print("\n[bold]SSL/TLS Certificate[/bold]")
    ssl_info = fetch_ssl_info(domain)
    _print_ssl(ssl_info)

    # ── WHOIS ─────────────────────────────────────────────────────────────────
    console.print("\n[bold]WHOIS Registration[/bold]")
    whois_info = fetch_whois(domain)
    if "error" in whois_info and whois_info["error"]:
        console.print(f"   [yellow]{whois_info['error']}[/yellow]")
    else:
        table = Table(
            show_header=False,
            border_style="bright_black",
            box=box.SIMPLE,
        )
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value")
        display_fields = [
            ("Registrar",       "registrar"),
            ("Created",         "creation_date"),
            ("Expires",         "expiration_date"),
            ("Updated",         "updated_date"),
            ("Name Servers",    "name_servers"),
            ("Registrant Org",  "org"),
            ("Country",         "country"),
            ("Status",          "status"),
        ]
        for label, key in display_fields:
            val = whois_info.get(key)
            if val:
                if isinstance(val, list):
                    display_val = ", ".join(val[:4]) + (" …" if len(val) > 4 else "")
                else:
                    display_val = str(val)
                table.add_row(label, display_val[:120])
        console.print(table)

    console.print()
    return {
        "domain": domain,
        "dns_records": dns_records,
        "ssl_info": ssl_info,
        "whois_info": whois_info,
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    run(target)
