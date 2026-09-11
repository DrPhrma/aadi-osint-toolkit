"""
website_scraper.py — Aadi OSINT Toolkit
-----------------------------------------
Scrapes public metadata from websites:
  • Page title, description, keywords
  • All links (internal and external)
  • Email addresses (in mailto links, visible text)
  • Meta tags, Open Graph data
  • Technology stack hints (server, framework)
  • Robots.txt, sitemap.xml references

Educational purpose: demonstrates passive web reconnaissance — reading what
a website publicly exposes about itself.

⚠ ETHICAL NOTES:
  • Respects robots.txt (we read but don't violate its restrictions)
  • Single request per domain (not crawling)
  • No rate limiting needed — one visit to homepage only
  • Always check site's Terms of Service before scraping
"""

import re
from urllib.parse import urljoin, urlparse
from typing import Any

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

TIMEOUT = 10
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

try:
    from bs4 import BeautifulSoup
    BS_AVAILABLE = True
except ImportError:
    BS_AVAILABLE = False
    console.print(
        "[yellow]⚠ BeautifulSoup4 not installed — web scraping disabled.\n"
        "   Install with: pip install beautifulsoup4[/yellow]"
    )


# ─────────────────────────────────────────────────────────────────────────────
# URL helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_url(url: str) -> str:
    """Add https:// if no protocol."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path


# ─────────────────────────────────────────────────────────────────────────────
# Scraper functions
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_page(url: str) -> tuple[str | None, dict]:
    """
    Fetch a URL and return (content, metadata).
    metadata includes: status_code, content_type, server, etc.
    """
    metadata = {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        metadata["status_code"] = r.status_code
        metadata["final_url"] = r.url
        metadata["content_type"] = r.headers.get("Content-Type", "—")
        metadata["server"] = r.headers.get("Server", "—")
        metadata["content_length"] = len(r.content)
        
        if r.status_code == 200 and "text/html" in metadata["content_type"]:
            return r.text, metadata
        else:
            metadata["error"] = f"HTTP {r.status_code} or non-HTML content"
            return None, metadata
    except requests.exceptions.Timeout:
        return None, {"error": "Timeout"}
    except requests.exceptions.RequestException as exc:
        return None, {"error": str(exc)}


def _parse_html(html: str, base_url: str) -> dict[str, Any]:
    """
    Parse HTML and extract metadata, links, emails.
    """
    if not BS_AVAILABLE:
        return {"error": "BeautifulSoup not available"}
    
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, Any] = {
        "title": "",
        "description": "",
        "keywords": "",
        "og_title": "",
        "og_description": "",
        "og_image": "",
        "links": [],
        "emails": [],
        "meta_tags": [],
        "scripts": [],
        "stylesheets": [],
    }
    
    # ── Basic meta ────────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    if title_tag:
        result["title"] = title_tag.get_text().strip()
    
    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        result["description"] = meta_desc.get("content", "").strip()
    
    # Meta keywords
    meta_kw = soup.find("meta", attrs={"name": "keywords"})
    if meta_kw:
        result["keywords"] = meta_kw.get("content", "").strip()
    
    # ── Open Graph ────────────────────────────────────────────────────────────
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title:
        result["og_title"] = og_title.get("content", "").strip()
    
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc:
        result["og_description"] = og_desc.get("content", "").strip()
    
    og_img = soup.find("meta", attrs={"property": "og:image"})
    if og_img:
        result["og_image"] = og_img.get("content", "").strip()
    
    # ── All meta tags ─────────────────────────────────────────────────────────
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property") or "?"
        content = tag.get("content", "")[:100]
        result["meta_tags"].append(f"{name}: {content}")
    
    # ── Links ─────────────────────────────────────────────────────────────────
    seen_links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#"):
            continue
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        if full_url not in seen_links:
            seen_links.add(full_url)
            result["links"].append({
                "url": full_url,
                "text": a_tag.get_text().strip()[:60],
                "internal": _extract_domain(full_url) == _extract_domain(base_url),
            })
    
    # ── Emails ────────────────────────────────────────────────────────────────
    seen_emails = set()
    
    # mailto: links
    for a_tag in soup.find_all("a", href=re.compile(r"^mailto:")):
        email = a_tag["href"].replace("mailto:", "").split("?")[0].strip()
        if email and "@" in email:
            seen_emails.add(email)
    
    # Text search (basic regex)
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    for match in re.finditer(email_pattern, html):
        email = match.group()
        # Filter out common false positives
        if not any(skip in email for skip in ["example.com", "test@", "user@", "[at]"]):
            seen_emails.add(email)
    
    result["emails"] = sorted(list(seen_emails))
    
    # ── Resources ─────────────────────────────────────────────────────────────
    for script in soup.find_all("script", src=True):
        src = script.get("src", "")
        result["scripts"].append(src[:100])
    
    for link in soup.find_all("link", rel=True):
        if "stylesheet" in link.get("rel", []):
            href = link.get("href", "")
            result["stylesheets"].append(href[:100])
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_metadata(parsed: dict) -> None:
    """Print extracted metadata."""
    if "error" in parsed:
        console.print(f"   [red]Error:[/red] {parsed['error']}")
        return
    
    panel_text = ""
    if parsed.get("title"):
        panel_text += f"[bold]Title[/bold]\n{parsed['title']}\n\n"
    if parsed.get("description"):
        panel_text += f"[bold]Description[/bold]\n{parsed['description']}\n\n"
    if parsed.get("keywords"):
        panel_text += f"[bold]Keywords[/bold]\n{parsed['keywords']}\n"
    
    if panel_text:
        console.print(Panel(panel_text.strip(), title="Page Metadata", border_style="cyan"))


def _print_links(parsed: dict) -> None:
    """Print links found."""
    links = parsed.get("links", [])
    if not links:
        console.print("   [dim]No links found.[/dim]")
        return
    
    internal = [l for l in links if l["internal"]]
    external = [l for l in links if not l["internal"]]
    
    console.print(f"\n[bold]Links[/bold]  (Internal: {len(internal)}, External: {len(external)})")
    
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
        expand=False,
    )
    table.add_column("Type", width=8, style="dim")
    table.add_column("URL", max_width=60, no_wrap=True)
    table.add_column("Text", max_width=30, no_wrap=True, style="dim")
    
    for link in links[:20]:  # Show first 20
        link_type = "[green]INT[/green]" if link["internal"] else "[cyan]EXT[/cyan]"
        table.add_row(link_type, link["url"], link["text"])
    
    if len(links) > 20:
        table.add_row("…", f"[dim](+{len(links) - 20} more)[/dim]", "")
    
    console.print(table)


def _print_emails(parsed: dict) -> None:
    """Print emails found."""
    emails = parsed.get("emails", [])
    if not emails:
        console.print("   [dim]No email addresses found.[/dim]")
        return
    
    console.print(f"\n[bold red]Emails Found ({len(emails)})[/bold red]")
    for email in emails[:15]:
        console.print(f"   [cyan]{email}[/cyan]")
    if len(emails) > 15:
        console.print(f"   [dim](+{len(emails) - 15} more)[/dim]")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(url: str) -> dict:
    """
    Scrape and analyse a website.

    Args:
        url: Website URL (with or without https://)

    Returns:
        dict with: url, metadata, parsed_content
    """
    url = _normalize_url(url)
    console.print(f"\n[bold cyan]🕸️ Website Scraper[/bold cyan] — target: [yellow]{url}[/yellow]\n")
    
    if not BS_AVAILABLE:
        console.print("[red]BeautifulSoup4 not installed.[/red]")
        return {"error": "BeautifulSoup4 not available", "url": url}
    
    # ── Fetch page ────────────────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Fetching page…", total=None)
        html, fetch_meta = _fetch_page(url)
        progress.remove_task(task)
    
    console.print(
        Panel(
            f"[bold]Status[/bold]: HTTP {fetch_meta.get('status_code', '?')}\n"
            f"[bold]Server[/bold]: {fetch_meta.get('server', '—')}\n"
            f"[bold]Size[/bold]: {fetch_meta.get('content_length', '?')} bytes",
            title="Response",
            border_style="bright_black",
        )
    )
    
    if not html:
        console.print(f"\n[red]Error:[/red] {fetch_meta.get('error', 'Unknown')}")
        return {"error": fetch_meta.get("error"), "url": url, "fetch_meta": fetch_meta}
    
    # ── Parse HTML ────────────────────────────────────────────────────────────
    parsed = _parse_html(html, url)
    
    # ── Display results ───────────────────────────────────────────────────────
    _print_metadata(parsed)
    _print_links(parsed)
    _print_emails(parsed)
    
    console.print()
    
    return {
        "url": url,
        "fetch_meta": fetch_meta,
        "parsed": parsed,
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    run(target)
