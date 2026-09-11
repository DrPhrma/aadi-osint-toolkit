"""
main.py — Aadi OSINT Toolkit
------------------------------
Main entry point with interactive CLI menu for all modules.

Legal notice:
    This tool uses ONLY public data sources and APIs.
    No hacking. No unauthorised access. No exploitation.
    For cybersecurity education purposes only.
"""

import sys
import os

# ── Rich library for beautiful terminal UI ────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich import box
    from rich.text import Text
    from rich.align import Align
except ImportError:
    print("ERROR: 'rich' library is not installed.")
    print("Run:  pip install rich")
    sys.exit(1)

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# ASCII Banner
# ─────────────────────────────────────────────────────────────────────────────

BANNER = r"""
  ____          ____  _____ _   _ _______   _______ ____   ____  _     _  _______ _______ 
 / __ \   /\   |  _ \|  __ \| \ | |_   _\ \ / / ____|  _ \ / __ \| |   | |/ /_   _|__   __|
| |  | | /  \  | |_) | |  | |  \| | | |  \ V /|  _| | |_) | |  | | |   | ' /  | |    | |   
| |  | |/ /\ \ |  _ <| |  | | . ` | | |   > < | |___|  _ <| |  | | |   |  <   | |    | |   
| |__| / ____ \| |_) | |__| | |\  |_| |_ / . \|_____|_| \_\ |__| | |___| . \ _| |_   | |   
 \____/_/    \_\____/|_____/|_| \_|_____/_/ \_\______|_|   \_\____/|_____|_|\_\_____|  |_|   
"""

TAGLINE = "  Open Source Intelligence Toolkit  ·  100% Legal  ·  Educational Use Only"


def print_banner() -> None:
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"[bold bright_black]{TAGLINE}[/bold bright_black]\n")


# ─────────────────────────────────────────────────────────────────────────────
# Menu
# ─────────────────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("1", "👤  Username Investigator",  "Check username presence across public websites"),
    ("2", "🌐  Domain Intelligence",    "DNS records, SSL certificate, WHOIS data"),
    ("3", "🖼   Image Metadata Analyzer","Extract EXIF data from image files"),
    ("4", "🔎  Public Keyword Tracker", "Search keyword mentions across public APIs"),
    ("5", "📧  Email Investigator",     "Check if email was leaked in data breaches"),
    ("6", "📍  IP Address Tracker",     "Geolocation, ISP, ASN info for an IP"),
    ("7", "📱  Phone Number Lookup",    "Validate phone, get carrier & timezone info"),
    ("8", "🕸️   Website Scraper",       "Extract links, emails, metadata from URL"),
    ("9", "🔗  URL Post Extractor",     "Paste Instagram/Twitter link → Extract ALL data"),
    ("10", "📄  Generate Full Report",  "Compile all results into TXT + HTML + CSV"),
    ("A", "❓  About / Help",           "How to use this toolkit"),
    ("0", "🚪  Exit",                   "Quit"),
]


def print_menu() -> None:
    table = Table(
        show_header=False,
        border_style="bright_black",
        box=box.SIMPLE,
        expand=False,
        padding=(0, 1),
    )
    table.add_column("Key", style="bold yellow", width=4)
    table.add_column("Module", style="bold")
    table.add_column("Description", style="dim")
    for key, name, desc in MENU_ITEMS:
        table.add_row(f"[{key}]", name, desc)
    console.print(Panel(table, title="[bold cyan]Main Menu[/bold cyan]", border_style="cyan"))


def print_about() -> None:
    text = (
        "[bold cyan]Aadi OSINT Toolkit[/bold cyan] — an educational, legal OSINT tool.\n\n"
        "[bold]What is OSINT?[/bold]\n"
        "Open Source Intelligence (OSINT) is the practice of collecting intelligence\n"
        "from publicly available sources: websites, DNS records, public APIs, etc.\n\n"
        "[bold]Modules:[/bold]\n"
        "  • [cyan]Username Investigator[/cyan]  — checks presence on 20+ public sites\n"
        "  • [cyan]Domain Intelligence[/cyan]    — DNS, SSL, WHOIS lookups\n"
        "  • [cyan]Image Metadata[/cyan]         — EXIF extraction (can reveal GPS!)\n"
        "  • [cyan]Keyword Tracker[/cyan]        — searches HN, Reddit, GitHub, Wikipedia, arXiv\n"
        "  • [cyan]Email Investigator[/cyan]     — checks Have I Been Pwned database\n"
        "  • [cyan]IP Address Tracker[/cyan]     — geolocation, ISP, ASN via ip-api.com\n"
        "  • [cyan]Phone Number Lookup[/cyan]    — validates phone, carrier, timezone\n"
        "  • [cyan]Website Scraper[/cyan]        — extracts metadata, links, emails from URLs\n"
        "  • [cyan]Report Generator[/cyan]       — combines all results into TXT + HTML + CSV\n\n"
        "[bold yellow]⚠ Legal & Ethical Use Only[/bold yellow]\n"
        "This tool ONLY queries publicly available data.\n"
        "Never use OSINT techniques on individuals without proper authorisation.\n"
        "Always comply with applicable laws and terms of service.\n\n"
        "[bold]Dependencies:[/bold]  pip install -r requirements.txt\n"
        "[bold]Config:[/bold]        Edit [cyan]sites_config.json[/cyan] to customize\n"
        "[bold]Reports:[/bold]       Saved to [cyan]reports/[/cyan] directory\n"
    )
    console.print(Panel(text, title="About / Help", border_style="bright_black"))


# ─────────────────────────────────────────────────────────────────────────────
# Module wrappers (lazy imports to keep startup fast)
# ─────────────────────────────────────────────────────────────────────────────

def run_username() -> dict | None:
    from username_checker import run
    username = Prompt.ask("\n  [bold yellow]Enter username[/bold yellow]").strip()
    if not username:
        console.print("[red]No username provided.[/red]")
        return None
    return run(username)


def run_domain() -> dict | None:
    from domain_intel import run
    domain = Prompt.ask("\n  [bold yellow]Enter domain[/bold yellow] (e.g. example.com)").strip()
    if not domain:
        console.print("[red]No domain provided.[/red]")
        return None
    return run(domain)


def run_image() -> dict | None:
    from image_metadata import run
    filepath = Prompt.ask("\n  [bold yellow]Enter image file path[/bold yellow]").strip()
    filepath = filepath.strip("'\"")
    if not filepath:
        console.print("[red]No path provided.[/red]")
        return None
    return run(filepath)


def run_keyword() -> dict | None:
    from keyword_tracker import run
    keyword = Prompt.ask("\n  [bold yellow]Enter keyword[/bold yellow]").strip()
    if not keyword:
        console.print("[red]No keyword provided.[/red]")
        return None
    return run(keyword)


def run_email() -> dict | None:
    from email_investigator import run
    email = Prompt.ask("\n  [bold yellow]Enter email address[/bold yellow]").strip()
    if not email:
        console.print("[red]No email provided.[/red]")
        return None
    return run(email)


def run_ip() -> dict | None:
    from ip_tracker import run
    ip = Prompt.ask("\n  [bold yellow]Enter IP address[/bold yellow]").strip()
    if not ip:
        console.print("[red]No IP provided.[/red]")
        return None
    return run(ip)


def run_phone() -> dict | None:
    from phone_lookup import run
    phone = Prompt.ask("\n  [bold yellow]Enter phone number[/bold yellow]").strip()
    if not phone:
        console.print("[red]No phone provided.[/red]")
        return None
    country = Prompt.ask("  [yellow]Country code (default: US)[/yellow]", default="US").strip().upper()
    return run(phone, country)


def run_website() -> dict | None:
    from website_scraper import run
    url = Prompt.ask("\n  [bold yellow]Enter website URL[/bold yellow]").strip()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return None
    return run(url)


def run_url_post() -> dict | None:
    from url_post_extractor import run
    url = Prompt.ask("\n  [bold yellow]Paste social media post URL[/bold yellow]").strip()
    if not url:
        console.print("[red]No URL provided.[/red]")
        return None
    return run(url)


def run_report(
    username_data: dict | None,
    domain_data: dict | None,
    image_data: dict | None,
    keyword_data: dict | None,
    email_data: dict | None = None,
    ip_data: dict | None = None,
    phone_data: dict | None = None,
    website_data: dict | None = None,
) -> None:
    if not any([username_data, domain_data, image_data, keyword_data,
                email_data, ip_data, phone_data, website_data]):
        console.print(
            "[yellow]No data collected yet.[/yellow] "
            "Run at least one module before generating a report."
        )
        return
    from report_generator import run
    run(username_data, domain_data, image_data, keyword_data,
        email_data, ip_data, phone_data, website_data)


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    console.clear()
    print_banner()

    username_data: dict | None = None
    domain_data: dict | None = None
    image_data: dict | None = None
    keyword_data: dict | None = None
    email_data: dict | None = None
    ip_data: dict | None = None
    phone_data: dict | None = None
    website_data: dict | None = None
    url_post_data: dict | None = None

    while True:
        print_menu()

        collected = []
        if username_data: collected.append(f"[green]user[/green]")
        if domain_data:   collected.append(f"[cyan]domain[/cyan]")
        if image_data:    collected.append(f"[magenta]image[/magenta]")
        if keyword_data:  collected.append(f"[yellow]kw[/yellow]")
        if email_data:    collected.append(f"[red]email[/red]")
        if ip_data:       collected.append(f"[blue]ip[/blue]")
        if phone_data:    collected.append(f"[bright_white]phone[/bright_white]")
        if website_data:  collected.append(f"[magenta]site[/magenta]")
        if url_post_data: collected.append(f"[bold yellow]post[/bold yellow]")
        if collected:
            console.print(f"  Session: {' · '.join(collected)}\n")

        choice = Prompt.ask("  [bold cyan]Select module[/bold cyan]", default="0").strip().upper()

        if choice == "1":
            result = run_username()
            if result and not result.get("error"):
                username_data = result
        elif choice == "2":
            result = run_domain()
            if result and not result.get("error"):
                domain_data = result
        elif choice == "3":
            result = run_image()
            if result and not result.get("error"):
                image_data = result
        elif choice == "4":
            result = run_keyword()
            if result and not result.get("error"):
                keyword_data = result
        elif choice == "5":
            result = run_email()
            if result and not result.get("error"):
                email_data = result
        elif choice == "6":
            result = run_ip()
            if result and not result.get("error"):
                ip_data = result
        elif choice == "7":
            result = run_phone()
            if result and not result.get("error"):
                phone_data = result
        elif choice == "8":
            result = run_website()
            if result and not result.get("error"):
                website_data = result
        elif choice == "9":
            result = run_url_post()
            if result and not result.get("error"):
                url_post_data = result
        elif choice == "10":
            run_report(username_data, domain_data, image_data, keyword_data,
                      email_data, ip_data, phone_data, website_data)
        elif choice == "A":
            print_about()
        elif choice == "0":
            if any([username_data, domain_data, image_data, keyword_data,
                   email_data, ip_data, phone_data, website_data, url_post_data]):
                if Confirm.ask("\n  Save a final report before exiting?", default=True):
                    run_report(username_data, domain_data, image_data, keyword_data,
                              email_data, ip_data, phone_data, website_data)
            console.print("\n[bold cyan]Goodbye. Stay ethical.[/bold cyan]\n")
            break
        else:
            console.print("[red]Invalid choice — enter 0–10, A.[/red]")

        console.print()


if __name__ == "__main__":
    main()
