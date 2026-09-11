"""
keyword_tracker.py — Aadi OSINT Toolkit
-----------------------------------------
Searches for public mentions of a keyword using free / open data sources:

  1. HackerNews Algolia API  — full-text search across HN stories and comments
  2. Wikipedia API           — article summaries and related pages
  3. Reddit public JSON API  — recent posts mentioning the keyword (no auth)
  4. GitHub public search    — public repos with the keyword in their description
  5. arXiv API               — academic papers (useful for technical OSINT)

All sources are 100% public and require no API keys.

Educational purpose: demonstrates aggregating public information from multiple
sources to build an intelligence picture — a core OSINT workflow.
"""

import time
from typing import Any
from datetime import datetime

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Polite HTTP timeout
TIMEOUT = 8
HEADERS = {
    "User-Agent": (
        "Aadi-OSINT-Toolkit/1.0 (educational project; "
        "https://github.com/aadi-osint) "
        "Python/3 requests"
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# Source fetchers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_hackernews(keyword: str, limit: int = 8) -> list[dict]:
    """
    Search HackerNews via the Algolia HN Search API (free, no key required).
    Returns a list of result dicts.
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": keyword, "hitsPerPage": limit, "tags": "story"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        results = []
        for hit in hits:
            ts = hit.get("created_at_i")
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") if ts else "—"
            results.append({
                "source": "HackerNews",
                "title": hit.get("title", "—")[:80],
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "author": hit.get("author", "—"),
                "date": date_str,
                "score": hit.get("points", 0),
            })
        return results
    except Exception as exc:
        return [{"source": "HackerNews", "error": str(exc)}]


def _fetch_wikipedia(keyword: str, limit: int = 5) -> list[dict]:
    """
    Search Wikipedia via its public REST API (no auth required).
    Returns article summaries.
    """
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": keyword,
        "srlimit": limit,
        "format": "json",
        "utf8": 1,
    }
    try:
        r = requests.get(search_url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        items = r.json().get("query", {}).get("search", [])
        results = []
        for item in items:
            title = item.get("title", "—")
            snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "")
            snippet = snippet.replace("</span>", "")[:120]
            results.append({
                "source": "Wikipedia",
                "title": title,
                "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "snippet": snippet,
                "date": "—",
            })
        return results
    except Exception as exc:
        return [{"source": "Wikipedia", "error": str(exc)}]


def _fetch_reddit(keyword: str, limit: int = 8) -> list[dict]:
    """
    Fetch public Reddit posts via the old.reddit.com JSON endpoint (no OAuth).
    Searches the r/all subreddit.
    """
    url = f"https://www.reddit.com/search.json"
    params = {"q": keyword, "sort": "relevance", "limit": limit, "type": "link"}
    # Reddit requires a descriptive User-Agent
    headers = {**HEADERS, "User-Agent": "Aadi-OSINT-Toolkit:v1.0 (educational)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        children = r.json().get("data", {}).get("children", [])
        results = []
        for child in children:
            d = child.get("data", {})
            ts = d.get("created_utc")
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") if ts else "—"
            results.append({
                "source": "Reddit",
                "title": d.get("title", "—")[:80],
                "url": "https://www.reddit.com" + d.get("permalink", ""),
                "author": d.get("author", "—"),
                "subreddit": d.get("subreddit_name_prefixed", "—"),
                "score": d.get("score", 0),
                "date": date_str,
            })
        return results
    except Exception as exc:
        return [{"source": "Reddit", "error": str(exc)}]


def _fetch_github(keyword: str, limit: int = 6) -> list[dict]:
    """
    Search GitHub public repos via the unauthenticated GitHub Search API.
    Unauthenticated: 10 requests/min — perfectly fine for single queries.
    """
    url = "https://api.github.com/search/repositories"
    params = {"q": keyword, "sort": "stars", "order": "desc", "per_page": limit}
    headers = {**HEADERS, "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        items = r.json().get("items", [])
        results = []
        for item in items:
            results.append({
                "source": "GitHub",
                "title": item.get("full_name", "—"),
                "url": item.get("html_url", "—"),
                "description": (item.get("description") or "")[:80],
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "—",
                "date": (item.get("pushed_at") or "")[:10],
            })
        return results
    except Exception as exc:
        return [{"source": "GitHub", "error": str(exc)}]


def _fetch_arxiv(keyword: str, limit: int = 5) -> list[dict]:
    """
    Search arXiv for academic papers via its public Atom/XML API.
    Great for technical OSINT on research topics.
    """
    import xml.etree.ElementTree as ET
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.text)
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", "—", ns).strip().replace("\n", " ")
            link_el = entry.find("atom:link[@rel='alternate']", ns)
            link = link_el.get("href") if link_el is not None else "—"
            authors = [a.findtext("atom:name", "", ns)
                       for a in entry.findall("atom:author", ns)]
            published = entry.findtext("atom:published", "—", ns)[:10]
            results.append({
                "source": "arXiv",
                "title": title[:80],
                "url": link,
                "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                "date": published,
            })
        return results
    except Exception as exc:
        return [{"source": "arXiv", "error": str(exc)}]


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

_SOURCE_COLORS = {
    "HackerNews": "bright_yellow",
    "Wikipedia":  "bright_blue",
    "Reddit":     "bright_red",
    "GitHub":     "bright_white",
    "arXiv":      "bright_cyan",
}


def _print_results(results: list[dict], source: str) -> None:
    color = _SOURCE_COLORS.get(source, "white")
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    if errors:
        console.print(f"   [red]{source} error:[/red] {errors[0]['error']}")
        return

    if not valid:
        console.print(f"   [dim]No results from {source}.[/dim]")
        return

    table = Table(
        title=f"[bold {color}]{source}[/bold {color}]  ({len(valid)} results)",
        show_header=True,
        header_style=f"bold {color}",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
        expand=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Title", max_width=55, no_wrap=True)
    table.add_column("Date", width=12)
    table.add_column("URL", max_width=50, no_wrap=True, style="dim")

    for idx, r in enumerate(valid, 1):
        table.add_row(str(idx), r.get("title", "—"), r.get("date", "—"), r.get("url", "—"))

    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

SOURCES = [
    ("HackerNews", _fetch_hackernews),
    ("Wikipedia",  _fetch_wikipedia),
    ("Reddit",     _fetch_reddit),
    ("GitHub",     _fetch_github),
    ("arXiv",      _fetch_arxiv),
]


def run(keyword: str) -> dict:
    """
    Track public keyword mentions across multiple open sources.

    Args:
        keyword: The search term.

    Returns:
        dict mapping source name → list of result dicts.
    """
    console.print(f"\n[bold cyan]🔎 Public Keyword Tracker[/bold cyan] — "
                  f"keyword: [yellow]\"{keyword}\"[/yellow]\n")

    all_results: dict[str, list[dict]] = {}
    total = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for source_name, fetcher in SOURCES:
            task = progress.add_task(f"Querying [cyan]{source_name}[/cyan]…", total=None)
            results = fetcher(keyword)
            all_results[source_name] = results
            progress.remove_task(task)
            time.sleep(0.3)  # be polite between API calls

    # Print results per source
    for source_name, _ in SOURCES:
        _print_results(all_results[source_name], source_name)
        valid = [r for r in all_results[source_name] if "error" not in r]
        total += len(valid)

    console.print(Panel(
        f"Keyword [bold yellow]\"{keyword}\"[/bold yellow] — "
        f"found [bold green]{total}[/bold green] public mentions across "
        f"{len(SOURCES)} sources.",
        border_style="cyan",
    ))

    return {"keyword": keyword, "results": all_results, "total_mentions": total}


if __name__ == "__main__":
    import sys
    kw = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "OSINT"
    run(kw)
