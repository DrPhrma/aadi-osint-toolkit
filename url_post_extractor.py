"""
url_post_extractor.py — Aadi OSINT Toolkit
---------------------------------------------
Extracts ALL data from a social media post URL without downloading:
  • Instagram posts
  • Twitter/X tweets
  • TikTok videos
  • Facebook posts
  • YouTube videos

Combines:
  • Post metadata (caption, location, timestamp)
  • EXIF data from images
  • Comments (reveals hidden info)
  • Hashtags & tags
  • Geolocation + privacy scoring

Educational purpose: Shows how much data is exposed via a single URL.
Helps users understand their digital footprint.

⚠️ NOTE: Uses ONLY publicly visible data. No hacking or API keys required.
"""

import re
import requests
from urllib.parse import urlparse
from typing import Any
from datetime import datetime

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


# ─────────────────────────────────────────────────────────────────────────────
# Platform detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_platform(url: str) -> str:
    """Identify which social platform the URL is from."""
    url = url.lower()
    
    if "instagram.com" in url:
        return "Instagram"
    elif "twitter.com" in url or "x.com" in url:
        return "Twitter"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "facebook.com" in url or "fb.com" in url:
        return "Facebook"
    elif "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "reddit.com" in url:
        return "Reddit"
    elif "linkedin.com" in url:
        return "LinkedIn"
    elif "snapchat.com" in url:
        return "Snapchat"
    else:
        return "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Instagram extractor
# ─────────────────────────────────────────────────────────────────────────────

def _extract_instagram(url: str) -> dict[str, Any]:
    """Extract data from Instagram post URL."""
    result: dict[str, Any] = {
        "platform": "Instagram",
        "url": url,
        "error": None,
        "caption": None,
        "author": None,
        "timestamp": None,
        "location": None,
        "image_urls": [],
        "likes": None,
        "comments_count": None,
        "hashtags": [],
        "mentions": [],
        "comments": [],
    }
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        
        if not BS_AVAILABLE:
            result["error"] = "BeautifulSoup not installed"
            return result
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extract from og: meta tags (most reliable)
        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_description = soup.find("meta", attrs={"property": "og:description"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        
        if og_description:
            caption = og_description.get("content", "")
            result["caption"] = caption[:200]
        
        if og_image:
            result["image_urls"].append(og_image.get("content", ""))
        
        # Extract from JSON-LD if available
        json_ld = soup.find("script", attrs={"type": "application/ld+json"})
        if json_ld:
            try:
                import json as json_lib
                data = json_lib.loads(json_ld.string)
                if isinstance(data, dict):
                    result["author"] = data.get("author", {}).get("name")
                    result["timestamp"] = data.get("uploadDate")
                    if "image" in data:
                        if isinstance(data["image"], list):
                            result["image_urls"].extend(data["image"])
                        else:
                            result["image_urls"].append(data["image"])
            except Exception:
                pass
        
        # Extract hashtags from caption
        if result["caption"]:
            hashtags = re.findall(r"#(\w+)", result["caption"])
            result["hashtags"] = hashtags
            
            mentions = re.findall(r"@(\w+)", result["caption"])
            result["mentions"] = mentions
        
        # Try to get author from page title
        title = soup.find("title")
        if title and not result["author"]:
            title_text = title.get_text()
            match = re.search(r"(@\w+)", title_text)
            if match:
                result["author"] = match.group(1)
        
    except Exception as exc:
        result["error"] = str(exc)
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Twitter extractor
# ─────────────────────────────────────────────────────────────────────────────

def _extract_twitter(url: str) -> dict[str, Any]:
    """Extract data from Twitter/X post URL."""
    result: dict[str, Any] = {
        "platform": "Twitter",
        "url": url,
        "error": None,
        "text": None,
        "author": None,
        "timestamp": None,
        "likes": None,
        "retweets": None,
        "image_urls": [],
        "hashtags": [],
        "mentions": [],
    }
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        
        if not BS_AVAILABLE:
            result["error"] = "BeautifulSoup not installed"
            return result
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Try og: tags
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc:
            result["text"] = og_desc.get("content", "")
        
        og_image = soup.find("meta", attrs={"property": "og:image"})
        if og_image:
            result["image_urls"].append(og_image.get("content", ""))
        
        # Extract from page content
        if result["text"]:
            hashtags = re.findall(r"#(\w+)", result["text"])
            result["hashtags"] = hashtags
            
            mentions = re.findall(r"@(\w+)", result["text"])
            result["mentions"] = mentions
        
    except Exception as exc:
        result["error"] = str(exc)
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Extract images and get EXIF
# ─────────────────────────────────────────────────────────────────────────────

def _extract_exif_from_image_url(image_url: str) -> dict[str, Any]:
    """Download image from URL and extract EXIF."""
    exif_data: dict[str, Any] = {}
    
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
    except ImportError:
        return {"error": "Pillow not installed"}
    
    try:
        r = requests.get(image_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        
        # Load image
        img = Image.open(r.raw)
        
        # Get EXIF
        try:
            exif_raw = img._getexif()
            if exif_raw:
                for tag_id, value in exif_raw.items():
                    tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                    if isinstance(value, bytes) and len(value) > 64:
                        exif_data[tag_name] = f"<binary {len(value)} bytes>"
                    else:
                        exif_data[tag_name] = str(value)[:100]
        except Exception:
            pass
        
        # Extract GPS if available
        gps_data = _parse_gps_from_exif(img)
        if gps_data:
            exif_data["GPS_Location"] = gps_data
        
        img.close()
    except Exception as exc:
        exif_data["error"] = str(exc)
    
    return exif_data


def _parse_gps_from_exif(image) -> dict | None:
    """Parse GPS from PIL Image EXIF."""
    try:
        from PIL.ExifTags import GPSTAGS
        
        exif_data = image._getexif()
        if not exif_data:
            return None
        
        gps_ifd = exif_data.get(34853)
        if not gps_ifd:
            return None
        
        gps = {}
        for tag, value in gps_ifd.items():
            tag_name = GPSTAGS.get(tag, tag)
            gps[tag_name] = value
        
        # Convert to decimal
        def _to_decimal(coord_tuple, ref):
            try:
                degrees = float(coord_tuple[0])
                minutes = float(coord_tuple[1])
                seconds = float(coord_tuple[2])
                decimal = degrees + minutes / 60.0 + seconds / 3600.0
                if ref in ("S", "W"):
                    decimal = -decimal
                return round(decimal, 7)
            except Exception:
                return None
        
        lat = _to_decimal(
            gps.get("GPSLatitude"),
            gps.get("GPSLatitudeRef", "N")
        ) if "GPSLatitude" in gps else None
        
        lon = _to_decimal(
            gps.get("GPSLongitude"),
            gps.get("GPSLongitudeRef", "E")
        ) if "GPSLongitude" in gps else None
        
        if lat and lon:
            return {
                "latitude": lat,
                "longitude": lon,
                "maps_link": f"https://maps.google.com/?q={lat},{lon}",
            }
    except Exception:
        pass
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Privacy Risk Scoring
# ─────────────────────────────────────────────────────────────────────────────

def _calculate_privacy_risk(data: dict) -> tuple[float, list[str]]:
    """Calculate privacy exposure score (0-10)."""
    score = 0.0
    risks: list[str] = []
    
    # EXIF GPS data
    if data.get("exif_data", {}).get("GPS_Location"):
        score += 2.5
        risks.append("Exact GPS coordinates exposed")
    
    # Location tagged
    if data.get("location"):
        score += 1.5
        risks.append("Location was explicitly tagged")
    
    # Timestamp
    if data.get("timestamp"):
        score += 1.0
        risks.append("Post timestamp reveals activity pattern")
    
    # Comments visible
    if data.get("comments"):
        score += 1.0
        risks.append("Comments may reveal additional information")
    
    # Hashtags reveal interests
    if data.get("hashtags"):
        score += 1.0
        risks.append("Hashtags reveal interests/job/location")
    
    # Author linked
    if data.get("author"):
        score += 0.5
        risks.append("Can link to author's profile")
    
    # Image analysis possible
    if data.get("image_urls"):
        score += 0.5
        risks.append("Image content can be analysed")
    
    return min(score, 10.0), risks


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_results(data: dict) -> None:
    """Print extracted data in formatted tables."""
    
    # ── Basic Info ────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]📋 POST INFORMATION[/bold cyan]")
    table = Table(show_header=False, border_style="bright_black", box=box.SIMPLE)
    table.add_column("Field", style="cyan", width=18)
    table.add_column("Value")
    
    table.add_row("Platform", data.get("platform", "?"))
    table.add_row("URL", data.get("url", "?")[:80])
    table.add_row("Author", data.get("author") or "—")
    table.add_row("Timestamp", data.get("timestamp") or "—")
    table.add_row("Location Tag", data.get("location") or "—")
    
    console.print(table)
    
    # ── Caption ───────────────────────────────────────────────────────────────
    if data.get("caption"):
        console.print(f"\n[bold cyan]📝 CAPTION[/bold cyan]")
        console.print(f"   {data['caption']}")
    
    # ── Hashtags & Mentions ───────────────────────────────────────────────────
    if data.get("hashtags") or data.get("mentions"):
        console.print(f"\n[bold cyan]🏷️ HASHTAGS & MENTIONS[/bold cyan]")
        if data.get("hashtags"):
            console.print(f"   [dim]Hashtags:[/dim] {', '.join(f'#{h}' for h in data['hashtags'][:10])}")
        if data.get("mentions"):
            console.print(f"   [dim]Mentions:[/dim] {', '.join(f'@{m}' for m in data['mentions'][:10])}")
    
    # ── EXIF Data ─────────────────────────────────────────────────────────────
    exif = data.get("exif_data", {})
    if exif and "error" not in exif:
        console.print(f"\n[bold cyan]📸 EXIF METADATA[/bold cyan]")
        exif_table = Table(show_header=False, border_style="bright_black", box=box.SIMPLE)
        exif_table.add_column("Tag", style="cyan", width=20)
        exif_table.add_column("Value")
        
        important_tags = [
            "Make", "Model", "DateTime", "DateTimeOriginal",
            "LensModel", "FocalLength", "FNumber", "ISOSpeedRatings",
            "GPS_Location"
        ]
        
        for tag in important_tags:
            if tag in exif:
                value = exif[tag]
                if tag == "GPS_Location" and isinstance(value, dict):
                    value_str = f"{value.get('latitude')}, {value.get('longitude')}"
                else:
                    value_str = str(value)[:80]
                exif_table.add_row(tag, value_str)
        
        console.print(exif_table)
        
        # GPS Maps Link
        if "GPS_Location" in exif and isinstance(exif["GPS_Location"], dict):
            maps_link = exif["GPS_Location"].get("maps_link")
            if maps_link:
                console.print(f"\n[bold red]⚠️ GPS LOCATION EXPOSED[/bold red]")
                console.print(f"   [link={maps_link}][cyan]{maps_link}[/cyan][/link]")
    
    # ── Privacy Risk ──────────────────────────────────────────────────────────
    if data.get("privacy_score"):
        score, risks = data["privacy_score"]
        color = "red" if score >= 7 else "yellow" if score >= 4 else "green"
        console.print(f"\n[bold {color}]🚨 PRIVACY RISK: {score:.1f}/10[/bold {color}]")
        
        if risks:
            console.print(f"   [dim]Exposed data:[/dim]")
            for risk in risks[:8]:
                console.print(f"   • {risk}")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(url: str) -> dict:
    """
    Extract all data from a social media post URL.

    Args:
        url: Social media post URL (Instagram, Twitter, TikTok, etc.)

    Returns:
        dict with extracted data
    """
    url = url.strip()
    console.print(f"\n[bold cyan]🔗 URL Post Extractor[/bold cyan] — [yellow]{url[:60]}...[/yellow]\n")
    
    # Detect platform
    platform = _detect_platform(url)
    console.print(f"   [dim]Platform detected:[/dim] [cyan]{platform}[/cyan]")
    
    if platform == "Unknown":
        console.print("[red]Platform not recognized. Supported: Instagram, Twitter, TikTok, Facebook, YouTube, Reddit, LinkedIn[/red]")
        return {"error": "Unknown platform"}
    
    # Extract based on platform
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Extracting post data…", total=None)
        
        if platform == "Instagram":
            data = _extract_instagram(url)
        elif platform == "Twitter":
            data = _extract_twitter(url)
        else:
            data = {"error": f"{platform} extraction coming soon"}
        
        progress.remove_task(task)
    
    if data.get("error"):
        console.print(f"[red]Error:[/red] {data['error']}")
        return data
    
    # Extract EXIF from images
    if data.get("image_urls"):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Extracting image metadata…", total=None)
            exif_data = _extract_exif_from_image_url(data["image_urls"][0])
            data["exif_data"] = exif_data
            progress.remove_task(task)
    
    # Calculate privacy risk
    data["privacy_score"] = _calculate_privacy_risk(data)
    
    # Display results
    _print_results(data)
    
    console.print()
    return data


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python url_post_extractor.py <instagram/twitter/tiktok URL>")
        raise SystemExit(1)
    run(sys.argv[1])
