"""
email_investigator.py — Aadi OSINT Toolkit
---------------------------------------------
Checks if an email address has been exposed in public data breaches using:
  • Have I Been Pwned API (Troy Hunt's free, no-auth API)
  • Email format validation
  • Basic syntax checks

Educational purpose: demonstrates how to find compromised credentials in the
wild — and why users should monitor their email accounts.

⚠ ETHICAL NOTE: Only use on your own email or with explicit permission.
"""

import re
from typing import Any

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Have I Been Pwned API endpoint
HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount"
HIBP_HEADER = {"User-Agent": "Aadi-OSINT-Toolkit"}

# Paste search API (checks if email was in pastes)
HIBP_PASTE_URL = "https://haveibeenpwned.com/api/v3/pasteaccount"


# ─────────────────────────────────────────────────────────────────────────────
# Email validation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _validate_email_format(email: str) -> tuple[bool, str]:
    """
    Basic RFC 5322-ish email validation.
    Returns (is_valid, error_message).
    """
    email = email.strip().lower()
    
    if not email:
        return False, "Email is empty"
    
    if len(email) > 254:
        return False, "Email too long (max 254 chars)"
    
    # Simple regex — not exhaustive but good for OSINT
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    local, domain = email.rsplit("@", 1)
    if len(local) > 64:
        return False, "Local part too long (max 64 chars)"
    
    if domain.startswith("-") or domain.endswith("-"):
        return False, "Domain cannot start/end with hyphen"
    
    return True, ""


def _check_hibp_breaches(email: str) -> list[dict]:
    """
    Query Have I Been Pwned for breaches.
    Returns list of breach info dicts.
    """
    params = {"includeUnverified": "false"}
    try:
        r = requests.get(
            HIBP_URL,
            params={**params, "account": email},
            headers=HIBP_HEADER,
            timeout=10,
        )
        
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            return []
        else:
            return []
    except Exception:
        return []


def _check_hibp_pastes(email: str) -> list[dict]:
    """
    Query Have I Been Pwned for paste sites.
    Returns list of paste info dicts.
    """
    try:
        r = requests.get(
            HIBP_PASTE_URL,
            params={"account": email},
            headers=HIBP_HEADER,
            timeout=10,
        )
        
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            return []
        else:
            return []
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_validation(email: str, is_valid: bool, error: str) -> None:
    """Print email format validation result."""
    if is_valid:
        console.print(
            Panel(
                f"[bold green]✔ Valid email format[/bold green]\n"
                f"Address: [cyan]{email}[/cyan]",
                title="Validation",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]✘ Invalid email format[/bold red]\n"
                f"Error: {error}",
                title="Validation",
                border_style="red",
            )
        )


def _print_breaches(breaches: list[dict]) -> None:
    """Print breach results."""
    if not breaches:
        console.print(
            Panel(
                "[bold green]✔ Good news! Email not found in any known breaches.[/bold green]",
                title="Breach Status",
                border_style="green",
            )
        )
        return
    
    console.print(
        Panel(
            f"[bold red]⚠ Email found in {len(breaches)} breach(es)![/bold red]",
            title="Breach Status",
            border_style="red",
        )
    )
    
    table = Table(
        show_header=True,
        header_style="bold red",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
        expand=False,
    )
    table.add_column("Breach Name", style="cyan", min_width=20)
    table.add_column("Date", width=12)
    table.add_column("Records", justify="right", style="yellow")
    table.add_column("Data Classes", max_width=40, no_wrap=True)
    
    for breach in breaches:
        name = breach.get("Name", "?")
        date = breach.get("BreachDate", "?")
        count = breach.get("PwnCount", 0)
        data_classes = ", ".join(breach.get("DataClasses", [])[:3])
        table.add_row(name, date, str(count), data_classes)
    
    console.print(table)


def _print_pastes(pastes: list[dict]) -> None:
    """Print paste site results."""
    if not pastes:
        console.print("   [dim]Email not found in any paste sites.[/dim]")
        return
    
    console.print(f"\n[bold red]⚠ Email found on {len(pastes)} paste site(s)![/bold red]")
    table = Table(
        show_header=True,
        header_style="bold red",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
        expand=False,
    )
    table.add_column("Site", style="cyan")
    table.add_column("Date", width=12)
    table.add_column("Title", max_width=50, no_wrap=True)
    
    for paste in pastes:
        site = paste.get("Source", "?")
        date = paste.get("PublicationDate", "")[:10] if paste.get("PublicationDate") else "?"
        title = paste.get("Title", "—")[:50]
        table.add_row(site, date, title)
    
    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(email: str) -> dict:
    """
    Investigate an email address for leaks and validity.

    Args:
        email: Email address to check

    Returns:
        dict with: email, is_valid, breaches, pastes
    """
    console.print(f"\n[bold cyan]📧 Email Investigator[/bold cyan] — target: [yellow]{email}[/yellow]\n")
    
    # ── Validate format ───────────────────────────────────────────────────────
    is_valid, error_msg = _validate_email_format(email)
    _print_validation(email, is_valid, error_msg)
    
    if not is_valid:
        return {
            "email": email,
            "is_valid": False,
            "error": error_msg,
            "breaches": [],
            "pastes": [],
        }
    
    # ── Check breaches ────────────────────────────────────────────────────────
    console.print("\n[bold]Checking Have I Been Pwned database…[/bold]")
    breaches = _check_hibp_breaches(email)
    _print_breaches(breaches)
    
    # ── Check pastes ──────────────────────────────────────────────────────────
    console.print("\n[bold]Checking paste sites…[/bold]")
    pastes = _check_hibp_pastes(email)
    _print_pastes(pastes)
    
    console.print()
    
    return {
        "email": email,
        "is_valid": True,
        "breaches": breaches,
        "pastes": pastes,
        "total_breaches": len(breaches),
        "total_pastes": len(pastes),
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    run(target)
