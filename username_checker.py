"""
username_checker.py — Aadi OSINT Toolkit
-----------------------------------------
Checks a given username across multiple public websites using HTTP HEAD/GET
requests. Sites are loaded from sites_config.json so you can add/remove them
without touching this file.

Educational purpose: demonstrates passive reconnaissance using only publicly
available information — no authentication, no exploitation.
"""

import json
import time
import os
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

# Path to the sites configuration file (same directory as this module)
SITES_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sites_config.json")

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 8

# Headers that mimic a real browser so sites don't block us outright
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def load_sites() -> list[dict]:
    """Load site definitions from the JSON config file."""
    try:
        with open(SITES_CONFIG, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("sites", [])
    except FileNotFoundError:
        console.print(f"[red]Config file not found:[/red] {SITES_CONFIG}")
        return []
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON in config:[/red] {exc}")
        return []


def check_single_site(site: dict, username: str) -> dict:
    """
    Probe a single site for the given username.

    Returns a dict with:
        name, category, url, found (bool), status_code, error
    """
    url = site["url"].replace("{username}", username)
    result = {
        "name": site["name"],
        "category": site.get("category", "Unknown"),
        "url": url,
        "found": False,
        "status_code": None,
        "error": None,
    }
    try:
        # Use GET so we get a proper status code; stream=True avoids downloading body
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
        result["status_code"] = response.status_code
        # 200 → likely found; anything else (404, 302-to-signup, etc.) → not found
        if response.status_code == 200:
            result["found"] = True
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection error"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.RequestException as exc:
        result["error"] = str(exc)[:60]
    return result


def run(username: str) -> dict:
    """
    Main entry point for the username checker.

    Args:
        username: The target username string.

    Returns:
        A dict with 'username', 'found', 'not_found', 'errors', 'results'.
    """
    sites = load_sites()
    if not sites:
        return {"error": "No sites loaded — check sites_config.json"}

    console.print(f"\n[bold cyan]🔍 Username Investigator[/bold cyan] — target: [yellow]{username}[/yellow]")
    console.print(f"   Checking {len(sites)} sites …\n")

    all_results: list[dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning sites", total=len(sites))
        for site in sites:
            progress.update(task, description=f"Checking [cyan]{site['name']}[/cyan]…")
            result = check_single_site(site, username)
            all_results.append(result)
            progress.advance(task)
            # Brief pause to be polite to remote servers
            time.sleep(0.2)

    # ── Summary table ──────────────────────────────────────────────────────────
    found = [r for r in all_results if r["found"]]
    not_found = [r for r in all_results if not r["found"] and not r["error"]]
    errors = [r for r in all_results if r["error"]]

    table = Table(
        title=f"Username: [bold yellow]{username}[/bold yellow]",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        expand=False,
    )
    table.add_column("Site", style="cyan", min_width=16)
    table.add_column("Category", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("HTTP", justify="right", style="dim")
    table.add_column("URL", style="dim", max_width=55, no_wrap=True)

    for r in all_results:
        if r["found"]:
            status = "[bold green]✔ FOUND[/bold green]"
        elif r["error"]:
            status = f"[red]✘ {r['error'][:20]}[/red]"
        else:
            status = "[dim]– not found[/dim]"

        http_code = str(r["status_code"]) if r["status_code"] else "—"
        table.add_row(r["name"], r["category"], status, http_code, r["url"])

    console.print(table)
    console.print(
        f"\n   [green]Found:[/green] {len(found)}  "
        f"[dim]Not found:[/dim] {len(not_found)}  "
        f"[red]Errors:[/red] {len(errors)}\n"
    )

    return {
        "username": username,
        "found": found,
        "not_found": not_found,
        "errors": errors,
        "results": all_results,
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "johndoe"
    run(target)
