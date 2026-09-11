"""
report_generator.py — Aadi OSINT Toolkit
------------------------------------------
Aggregates outputs from all modules and generates:
  • A formatted plain-text report  (.txt)
  • A styled, self-contained HTML report  (.html)

Educational purpose: demonstrates assembling multi-source intelligence into
a structured, readable document — a core deliverable in OSINT engagements.
"""

import os
import json
import csv
import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel

console = Console()

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_report_dir() -> None:
    os.makedirs(REPORT_DIR, exist_ok=True)


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_str(val: Any, max_len: int = 200) -> str:
    if val is None:
        return "—"
    s = str(val)
    return s[:max_len] + ("…" if len(s) > max_len else "")


# ─────────────────────────────────────────────────────────────────────────────
# TXT Report
# ─────────────────────────────────────────────────────────────────────────────

def _build_txt(
    username_data: dict | None,
    domain_data: dict | None,
    image_data: dict | None,
    keyword_data: dict | None,
) -> str:
    lines: list[str] = []
    divider = "=" * 72
    thin_div = "-" * 72

    lines.append(divider)
    lines.append("   AADI OSINT TOOLKIT — INTELLIGENCE REPORT")
    lines.append(f"   Generated: {_timestamp()}")
    lines.append(divider)
    lines.append("")

    # ── 1. Summary ────────────────────────────────────────────────────────────
    lines.append("SECTION 1 — TARGET SUMMARY")
    lines.append(thin_div)
    if username_data:
        lines.append(f"  Username  : {username_data.get('username', '—')}")
        found_count = len(username_data.get("found", []))
        total = len(username_data.get("results", []))
        lines.append(f"  Presence  : {found_count}/{total} sites confirmed")
    if domain_data:
        lines.append(f"  Domain    : {domain_data.get('domain', '—')}")
    if image_data:
        lines.append(f"  Image     : {os.path.basename(image_data.get('filepath', '—'))}")
    if keyword_data:
        lines.append(f"  Keyword   : \"{keyword_data.get('keyword', '—')}\"")
        lines.append(f"  Mentions  : {keyword_data.get('total_mentions', 0)} public results")
    lines.append("")

    # ── 2. Username Results ───────────────────────────────────────────────────
    if username_data and not username_data.get("error"):
        lines.append("SECTION 2 — USERNAME INVESTIGATION")
        lines.append(thin_div)
        found = username_data.get("found", [])
        lines.append(f"  Username: {username_data['username']}")
        lines.append(f"  Found on {len(found)} sites:")
        lines.append("")
        for r in found:
            lines.append(f"    [{r['category']}] {r['name']}")
            lines.append(f"       URL: {r['url']}")
        errors = username_data.get("errors", [])
        if errors:
            lines.append(f"\n  Errors on {len(errors)} sites (unreachable / timeout):")
            for r in errors:
                lines.append(f"    • {r['name']}: {r.get('error', '?')}")
        lines.append("")

    # ── 3. Domain Intelligence ────────────────────────────────────────────────
    if domain_data and not domain_data.get("error"):
        lines.append("SECTION 3 — DOMAIN INTELLIGENCE")
        lines.append(thin_div)
        lines.append(f"  Domain: {domain_data['domain']}")

        dns = domain_data.get("dns_records", {})
        if dns:
            lines.append("\n  DNS Records:")
            for rtype, values in dns.items():
                for v in values:
                    lines.append(f"    {rtype:<8} {v}")

        ssl = domain_data.get("ssl_info", {})
        if ssl and not ssl.get("error"):
            lines.append("\n  SSL Certificate:")
            subj = ssl.get("subject", {})
            issuer = ssl.get("issuer", {})
            lines.append(f"    Subject  : {subj.get('commonName', '—')}")
            lines.append(f"    Issuer   : {issuer.get('organizationName', '—')}")
            lines.append(f"    Valid to : {ssl.get('not_after', '—')}  ({ssl.get('days_until_expiry', '?')} days left)")
            lines.append(f"    Cipher   : {ssl.get('cipher_name', '—')} / {ssl.get('tls_version', '—')}")
            sans = ssl.get("subject_alt_names", [])
            if sans:
                lines.append(f"    SANs     : {', '.join(sans[:6])}")

        whois = domain_data.get("whois_info", {})
        if whois and not whois.get("error"):
            lines.append("\n  WHOIS:")
            for key, label in [
                ("registrar", "Registrar"),
                ("creation_date", "Created"),
                ("expiration_date", "Expires"),
                ("org", "Org"),
                ("country", "Country"),
            ]:
                val = whois.get(key)
                if val:
                    lines.append(f"    {label:<12}: {_safe_str(val, 80)}")
        lines.append("")

    # ── 4. Image Metadata ─────────────────────────────────────────────────────
    if image_data and not image_data.get("error"):
        lines.append("SECTION 4 — IMAGE METADATA")
        lines.append(thin_div)
        fm = image_data.get("file_meta", {})
        lines.append(f"  File      : {fm.get('filename', '—')}")
        lines.append(f"  Size      : {fm.get('size_human', '—')}")
        lines.append(f"  Dimensions: {fm.get('dimensions', '—')}")
        lines.append(f"  Format    : {fm.get('pil_format', '—')}")

        exif = image_data.get("exif", {})
        interesting = [
            ("Make", "Camera Make"),
            ("Model", "Camera Model"),
            ("Software", "Software"),
            ("DateTimeOriginal", "Capture Time"),
            ("DateTime", "DateTime"),
            ("LensModel", "Lens"),
            ("ISOSpeedRatings", "ISO"),
            ("FNumber", "F-Number"),
            ("FocalLength", "Focal Length"),
            ("Artist", "Artist"),
        ]
        exif_lines = []
        for key, label in interesting:
            if key in exif:
                exif_lines.append(f"    {label:<14}: {_safe_str(exif[key], 60)}")
        if exif_lines:
            lines.append("\n  EXIF Data:")
            lines.extend(exif_lines)

        gps = image_data.get("gps_info")
        if gps and "DecimalLatitude" in gps:
            lines.append("\n  ⚠  GPS Location Data Found!")
            lines.append(f"    Latitude : {gps['DecimalLatitude']}")
            lines.append(f"    Longitude: {gps['DecimalLongitude']}")
            lines.append(f"    Map link : {gps.get('GoogleMapsLink', '—')}")
        lines.append("")

    # ── 5. Keyword Results ────────────────────────────────────────────────────
    if keyword_data and not keyword_data.get("error"):
        lines.append("SECTION 5 — PUBLIC KEYWORD TRACKER")
        lines.append(thin_div)
        lines.append(f"  Keyword: \"{keyword_data['keyword']}\"")
        lines.append(f"  Total mentions: {keyword_data.get('total_mentions', 0)}\n")
        for source, results in keyword_data.get("results", {}).items():
            valid = [r for r in results if "error" not in r]
            if not valid:
                continue
            lines.append(f"  [{source}] — {len(valid)} results:")
            for r in valid[:5]:
                lines.append(f"    • {r.get('title', '—')[:70]}")
                lines.append(f"      {r.get('url', '—')}")
        lines.append("")

    lines.append(divider)
    lines.append("  END OF REPORT — Aadi OSINT Toolkit  |  For educational use only")
    lines.append(divider)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# HTML Report
# ─────────────────────────────────────────────────────────────────────────────

def _build_html(
    username_data: dict | None,
    domain_data: dict | None,
    image_data: dict | None,
    keyword_data: dict | None,
) -> str:
    ts = _timestamp()

    def section(title: str, icon: str, content: str) -> str:
        return f"""
        <section>
          <h2>{icon} {title}</h2>
          <div class="section-body">{content}</div>
        </section>"""

    def kv(label: str, value: Any) -> str:
        return f'<tr><td class="label">{label}</td><td>{_safe_str(value, 200)}</td></tr>'

    def table_open(headers: list[str]) -> str:
        ths = "".join(f"<th>{h}</th>" for h in headers)
        return f'<table><thead><tr>{ths}</tr></thead><tbody>'

    def table_close() -> str:
        return "</tbody></table>"

    # ── Summary section ───────────────────────────────────────────────────────
    sum_rows = ""
    if username_data:
        found_count = len(username_data.get("found", []))
        total = len(username_data.get("results", []))
        sum_rows += kv("Username", username_data.get("username", "—"))
        sum_rows += kv("Sites Checked", f"{found_count}/{total} found")
    if domain_data:
        sum_rows += kv("Domain", domain_data.get("domain", "—"))
    if image_data:
        sum_rows += kv("Image File", os.path.basename(image_data.get("filepath", "—")))
    if keyword_data:
        sum_rows += kv("Keyword", f'"{keyword_data.get("keyword", "—")}"')
        sum_rows += kv("Total Mentions", keyword_data.get("total_mentions", 0))
    summary_html = f"<table>{sum_rows}</table>"

    # ── Username section ──────────────────────────────────────────────────────
    username_html = ""
    if username_data and not username_data.get("error"):
        found = username_data.get("found", [])
        username_html = f"<p><strong>{len(found)}</strong> sites confirmed for username <strong>{username_data['username']}</strong></p>"
        if found:
            username_html += table_open(["Site", "Category", "URL"])
            for r in found:
                username_html += (
                    f'<tr><td>{r["name"]}</td><td>{r["category"]}</td>'
                    f'<td><a href="{r["url"]}" target="_blank">{r["url"]}</a></td></tr>'
                )
            username_html += table_close()

    # ── Domain section ────────────────────────────────────────────────────────
    domain_html = ""
    if domain_data and not domain_data.get("error"):
        dns = domain_data.get("dns_records", {})
        d_rows = ""
        for rtype, values in dns.items():
            for v in values:
                d_rows += f"<tr><td><strong>{rtype}</strong></td><td>{v}</td></tr>"
        domain_html = f"<h3>DNS Records</h3><table>{d_rows}</table>" if d_rows else ""

        ssl = domain_data.get("ssl_info", {})
        if ssl and not ssl.get("error"):
            days = ssl.get("days_until_expiry", 0)
            exp_color = "green" if days and days > 30 else "red"
            subj = ssl.get("subject", {})
            issuer = ssl.get("issuer", {})
            ssl_rows = (
                kv("Subject CN", subj.get("commonName", "—"))
                + kv("Issuer", issuer.get("organizationName", "—"))
                + kv("Valid Until", f'{ssl.get("not_after","—")} '
                     f'(<span style="color:{exp_color}">{days} days</span>)')
                + kv("TLS Version", ssl.get("tls_version", "—"))
                + kv("Cipher", ssl.get("cipher_name", "—"))
            )
            sans = ssl.get("subject_alt_names", [])
            if sans:
                ssl_rows += kv("SANs", ", ".join(sans[:8]))
            domain_html += f"<h3>SSL Certificate</h3><table>{ssl_rows}</table>"

    # ── Image section ─────────────────────────────────────────────────────────
    image_html = ""
    if image_data and not image_data.get("error"):
        fm = image_data.get("file_meta", {})
        img_rows = (
            kv("Filename", fm.get("filename", "—"))
            + kv("Size", fm.get("size_human", "—"))
            + kv("Dimensions", fm.get("dimensions", "—"))
            + kv("Format", fm.get("pil_format", "—"))
        )
        exif = image_data.get("exif", {})
        for tag in ["Make", "Model", "Software", "DateTimeOriginal", "LensModel",
                    "ISOSpeedRatings", "FNumber", "FocalLength", "Artist"]:
            if tag in exif:
                img_rows += kv(tag, exif[tag])
        image_html = f"<table>{img_rows}</table>"

        gps = image_data.get("gps_info")
        if gps and "DecimalLatitude" in gps:
            lat, lon = gps["DecimalLatitude"], gps["DecimalLongitude"]
            link = gps.get("GoogleMapsLink", "")
            image_html += (
                f'<div class="gps-alert">⚠ <strong>GPS Data Found!</strong><br>'
                f'Lat: {lat} | Lon: {lon}<br>'
                f'<a href="{link}" target="_blank">Open in Google Maps ↗</a></div>'
            )

    # ── Keyword section ───────────────────────────────────────────────────────
    keyword_html = ""
    if keyword_data and not keyword_data.get("error"):
        keyword_html = f"<p>Keyword: <strong>\"{keyword_data['keyword']}\"</strong> — " \
                       f"<strong>{keyword_data.get('total_mentions', 0)}</strong> total mentions</p>"
        for source, results in keyword_data.get("results", {}).items():
            valid = [r for r in results if "error" not in r]
            if not valid:
                continue
            keyword_html += f"<h3>{source} ({len(valid)} results)</h3>"
            keyword_html += table_open(["Title", "Date", "URL"])
            for r in valid[:6]:
                url = r.get("url", "#")
                title = r.get("title", "—")
                date = r.get("date", "—")
                keyword_html += (
                    f'<tr><td>{title}</td><td>{date}</td>'
                    f'<td><a href="{url}" target="_blank">{url[:60]}…</a></td></tr>'
                )
            keyword_html += table_close()

    # ── Assemble HTML ─────────────────────────────────────────────────────────
    sections = ""
    sections += section("Target Summary", "🎯", summary_html)
    if username_html:
        sections += section("Username Investigation", "👤", username_html)
    if domain_html:
        sections += section("Domain Intelligence", "🌐", domain_html)
    if image_html:
        sections += section("Image Metadata", "🖼", image_html)
    if keyword_html:
        sections += section("Public Keyword Tracker", "🔎", keyword_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aadi OSINT Toolkit — Intelligence Report</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --accent: #58a6ff; --accent2: #3fb950;
    --text: #e6edf3; --muted: #8b949e;
    --warn: #f0883e; --danger: #f85149;
    --font: "Segoe UI", system-ui, sans-serif;
    --mono: "Cascadia Code", "Fira Code", monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--font); line-height: 1.6; }}
  header {{ background: linear-gradient(135deg, #0d1117 0%, #161b22 60%, #1a2030 100%);
            border-bottom: 1px solid var(--border); padding: 2rem 2.5rem 1.5rem; }}
  .banner {{ font-family: var(--mono); font-size: 0.7rem; color: var(--accent); white-space: pre; line-height: 1.2; margin-bottom: 1rem; }}
  header h1 {{ font-size: 1.8rem; color: var(--accent); }}
  header .meta {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.3rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 2rem 4rem; }}
  section {{ background: var(--surface); border: 1px solid var(--border);
             border-radius: 8px; margin-bottom: 1.5rem; overflow: hidden; }}
  section h2 {{ padding: 0.8rem 1.2rem; background: #1c2128; border-bottom: 1px solid var(--border);
                font-size: 1rem; color: var(--accent); }}
  .section-body {{ padding: 1.2rem; }}
  section h3 {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.05em; margin: 1rem 0 0.5rem; }}
  section h3:first-child {{ margin-top: 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ background: #1c2128; color: var(--muted); font-weight: 600;
        text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); }}
  td {{ padding: 0.45rem 0.75rem; border-bottom: 1px solid #21262d; vertical-align: top; }}
  td.label {{ color: var(--muted); font-size: 0.82rem; white-space: nowrap; width: 180px; }}
  tr:last-child td {{ border-bottom: none; }}
  a {{ color: var(--accent); text-decoration: none; word-break: break-all; }}
  a:hover {{ text-decoration: underline; }}
  .gps-alert {{ background: #2d1515; border: 1px solid var(--danger);
                border-radius: 6px; padding: 1rem; margin-top: 1rem;
                color: var(--warn); font-size: 0.9rem; line-height: 1.8; }}
  .gps-alert a {{ color: var(--accent2); }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.78rem;
            padding: 1.5rem; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<header>
<pre class="banner">
  ____          ____ ____  _   _ _____   _____           _ _    _ _   
 / __ \\   /\\   |  _ \\___ \\| \\ | |_   _| |_   _|         | | |  (_) |  
| |  | | /  \\  | |_) |__) |  \\| | | |     | | ___   ___ | | | ___| |_ 
| |  | |/ /\\ \\ |  _ <|__ <| . ` | | |     | |/ _ \\ / _ \\| | |/ / | __|
| |__| / ____ \\| |_) |__) | |\\  |_| |_    | | (_) | (_) | |   <| | |_ 
 \\____/_/    \\_\\____/____/|_| \\_|_____|   |_|\\___/ \\___/|_|_|\\_\\_|\\__|
</pre>
  <h1>Intelligence Report</h1>
  <p class="meta">Generated: {ts} &nbsp;|&nbsp; Aadi OSINT Toolkit &nbsp;|&nbsp; Educational use only</p>
</header>
<main>{sections}</main>
<footer>Aadi OSINT Toolkit — 100% Legal, Ethical, Open-Source Intelligence Only<br>
No unauthorized access. No exploitation. Public data sources only.</footer>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# CSV Export
# ─────────────────────────────────────────────────────────────────────────────

def _export_csv(
    username_data: dict | None = None,
    domain_data: dict | None = None,
    image_data: dict | None = None,
    keyword_data: dict | None = None,
    email_data: dict | None = None,
    ip_data: dict | None = None,
    phone_data: dict | None = None,
    website_data: dict | None = None,
) -> str:
    """Export all results as CSV."""
    csv_path = os.path.join(REPORT_DIR, f"osint_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    rows = []
    
    # Username results
    if username_data and not username_data.get("error"):
        for r in username_data.get("found", []):
            rows.append({
                "Type": "Username",
                "Target": username_data.get("username"),
                "Field": r.get("name"),
                "Category": r.get("category"),
                "Value": r.get("url"),
                "Status": "FOUND",
            })
    
    # Email results
    if email_data and not email_data.get("error"):
        rows.append({
            "Type": "Email",
            "Target": email_data.get("email"),
            "Field": "Validation",
            "Category": "Email",
            "Value": "Valid" if email_data.get("is_valid") else "Invalid",
            "Status": "OK",
        })
        for breach in email_data.get("breaches", []):
            rows.append({
                "Type": "Email",
                "Target": email_data.get("email"),
                "Field": "Breach",
                "Category": breach.get("Name"),
                "Value": breach.get("BreachDate"),
                "Status": "LEAKED",
            })
    
    # IP results
    if ip_data and not ip_data.get("error"):
        loc = ip_data.get("location_data", {})
        rows.append({
            "Type": "IP",
            "Target": ip_data.get("ip"),
            "Field": "Country",
            "Category": "Geolocation",
            "Value": loc.get("country"),
            "Status": "OK",
        })
    
    # Write CSV
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Type", "Target", "Field", "Category", "Value", "Status"])
            writer.writeheader()
            writer.writerows(rows)
    
    return csv_path


def run(
    username_data: dict | None = None,
    domain_data: dict | None = None,
    image_data: dict | None = None,
    keyword_data: dict | None = None,
    email_data: dict | None = None,
    ip_data: dict | None = None,
    phone_data: dict | None = None,
    website_data: dict | None = None,
) -> dict:
    """
    Generate TXT, HTML, and CSV reports from collected module data.

    Returns:
        dict with 'txt_path', 'html_path', 'csv_path'.
    """
    _ensure_report_dir()
    ts_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    txt_path = os.path.join(REPORT_DIR, f"osint_report_{ts_file}.txt")
    html_path = os.path.join(REPORT_DIR, f"osint_report_{ts_file}.html")

    txt_content = _build_txt(username_data, domain_data, image_data, keyword_data)
    html_content = _build_html(username_data, domain_data, image_data, keyword_data)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Export CSV
    csv_path = _export_csv(username_data, domain_data, image_data, keyword_data,
                           email_data, ip_data, phone_data, website_data)

    console.print(Panel(
        f"[bold green]✔ Reports saved![/bold green]\n\n"
        f"  [cyan]TXT:[/cyan]   {txt_path}\n"
        f"  [cyan]HTML:[/cyan]  {html_path}\n"
        f"  [cyan]CSV:[/cyan]   {csv_path}",
        title="Report Generator",
        border_style="green",
    ))

    return {"txt_path": txt_path, "html_path": html_path, "csv_path": csv_path}
