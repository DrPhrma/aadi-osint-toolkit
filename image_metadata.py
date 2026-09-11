"""
image_metadata.py — Aadi OSINT Toolkit
----------------------------------------
Extracts EXIF and file-level metadata from image files using Pillow (PIL).
EXIF data is embedded by cameras, phones, and editing software.  It can reveal:
  • Camera make / model
  • Capture date and time
  • GPS coordinates (if location services were enabled on the device)
  • Lens settings (focal length, aperture, ISO)
  • Software used to edit the image

Educational purpose: demonstrates how much information can be recovered from
a seemingly plain image file — and why scrubbing EXIF before sharing matters.

⚠ GPS data can reveal physical locations — handle responsibly.
"""

import os
import struct
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    console.print(
        "[yellow]⚠  Pillow not installed — image metadata extraction disabled.\n"
        "   Install with: pip install Pillow[/yellow]"
    )


# ─────────────────────────────────────────────────────────────────────────────
# EXIF extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_exif_raw(image: "Image.Image") -> dict[str, Any]:
    """Return a human-readable dict of all EXIF tags from a Pillow Image."""
    raw: dict[str, Any] = {}
    try:
        exif_data = image._getexif()  # returns None for non-JPEG or missing EXIF
        if not exif_data:
            return {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
            # Skip binary blobs (MakerNote, UserComment raw bytes, etc.)
            if isinstance(value, bytes) and len(value) > 64:
                raw[tag_name] = f"<binary {len(value)} bytes>"
            else:
                raw[tag_name] = value
    except Exception:
        pass
    return raw


def _parse_gps(gps_info_raw: Any) -> dict[str, Any] | None:
    """
    Decode the GPSInfo sub-IFD into a readable dict with decimal coordinates.
    Returns None if gps_info_raw is not valid GPS data.
    """
    if not isinstance(gps_info_raw, dict):
        return None

    gps_labeled: dict[str, Any] = {}
    for tag_id, value in gps_info_raw.items():
        tag_name = GPSTAGS.get(tag_id, f"GPS_{tag_id}")
        gps_labeled[tag_name] = value

    def _to_decimal(coord_tuple, ref: str) -> float | None:
        """Convert DMS (degrees, minutes, seconds) tuple to decimal degrees."""
        try:
            if hasattr(coord_tuple[0], "numerator"):
                # IFDRational objects
                degrees = float(coord_tuple[0])
                minutes = float(coord_tuple[1])
                seconds = float(coord_tuple[2])
            else:
                degrees, minutes, seconds = coord_tuple
            decimal = degrees + minutes / 60.0 + seconds / 3600.0
            if ref in ("S", "W"):
                decimal = -decimal
            return round(decimal, 7)
        except Exception:
            return None

    lat = _to_decimal(
        gps_labeled.get("GPSLatitude"),
        gps_labeled.get("GPSLatitudeRef", "N"),
    ) if "GPSLatitude" in gps_labeled else None

    lon = _to_decimal(
        gps_labeled.get("GPSLongitude"),
        gps_labeled.get("GPSLongitudeRef", "E"),
    ) if "GPSLongitude" in gps_labeled else None

    gps_out: dict[str, Any] = {k: str(v) for k, v in gps_labeled.items()}
    if lat is not None and lon is not None:
        gps_out["DecimalLatitude"] = lat
        gps_out["DecimalLongitude"] = lon
        gps_out["GoogleMapsLink"] = f"https://maps.google.com/?q={lat},{lon}"
    return gps_out


# ─────────────────────────────────────────────────────────────────────────────
# File-level metadata (no EXIF library needed)
# ─────────────────────────────────────────────────────────────────────────────

def _file_metadata(filepath: str) -> dict[str, Any]:
    """Return basic OS-level file metadata."""
    import datetime
    stat = os.stat(filepath)
    return {
        "filename": os.path.basename(filepath),
        "filepath": os.path.abspath(filepath),
        "size_bytes": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "created": datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def _human_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

# EXIF fields considered "interesting" for OSINT — shown in a highlight table
HIGHLIGHT_FIELDS = [
    ("Make",              "Camera Make"),
    ("Model",             "Camera Model"),
    ("Software",          "Software"),
    ("DateTime",          "Capture Date/Time"),
    ("DateTimeOriginal",  "Original Date/Time"),
    ("DateTimeDigitized", "Digitized Date/Time"),
    ("ImageWidth",        "Image Width"),
    ("ImageLength",       "Image Height"),
    ("Orientation",       "Orientation"),
    ("Flash",             "Flash"),
    ("FocalLength",       "Focal Length"),
    ("FNumber",           "F-Number (Aperture)"),
    ("ISOSpeedRatings",   "ISO Speed"),
    ("ExposureTime",      "Exposure Time"),
    ("WhiteBalance",      "White Balance"),
    ("LensModel",         "Lens Model"),
    ("GPSInfo",           "GPS Data present"),
    ("Artist",            "Artist / Author"),
    ("Copyright",         "Copyright"),
    ("ImageDescription",  "Image Description"),
    ("UserComment",       "User Comment"),
    ("XPAuthor",          "XP Author"),
    ("XPComment",         "XP Comment"),
    ("XPTitle",           "XP Title"),
]


def _print_highlight_table(exif: dict[str, Any]) -> None:
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        box=box.SIMPLE_HEAD,
        expand=False,
    )
    table.add_column("Field", style="cyan", min_width=22)
    table.add_column("Value")

    for exif_key, label in HIGHLIGHT_FIELDS:
        val = exif.get(exif_key)
        if val is None:
            continue
        if exif_key == "GPSInfo":
            display = "[green]✔ GPS coordinates embedded[/green]"
        elif isinstance(val, bytes):
            display = f"<bytes {len(val)}>"
        else:
            display = str(val)[:160]
        table.add_row(label, display)

    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(filepath: str) -> dict:
    """
    Analyse image metadata and print a formatted report.

    Args:
        filepath: Absolute or relative path to an image file.

    Returns:
        dict with keys: filepath, file_meta, exif, gps_info
    """
    if not os.path.isfile(filepath):
        console.print(f"[red]File not found:[/red] {filepath}")
        return {"error": f"File not found: {filepath}"}

    console.print(f"\n[bold cyan]🖼  Image Metadata Analyzer[/bold cyan] — [yellow]{os.path.basename(filepath)}[/yellow]\n")

    # ── File-level info ───────────────────────────────────────────────────────
    file_meta = _file_metadata(filepath)
    console.print(Panel(
        f"[bold]Path    :[/bold] {file_meta['filepath']}\n"
        f"[bold]Size    :[/bold] {file_meta['size_human']}  ({file_meta['size_bytes']:,} bytes)\n"
        f"[bold]Modified:[/bold] {file_meta['modified']}\n"
        f"[bold]Created :[/bold] {file_meta['created']}",
        title="File Info",
        border_style="bright_black",
    ))

    if not PILLOW_AVAILABLE:
        console.print("[yellow]Install Pillow to extract EXIF data.[/yellow]")
        return {"filepath": filepath, "file_meta": file_meta, "exif": {}, "gps_info": None}

    # ── Open with Pillow ──────────────────────────────────────────────────────
    try:
        img = Image.open(filepath)
    except Exception as exc:
        console.print(f"[red]Cannot open image:[/red] {exc}")
        return {"filepath": filepath, "file_meta": file_meta, "exif": {}, "gps_info": None, "error": str(exc)}

    # Image dimensions from Pillow (works for all formats)
    file_meta["pil_format"] = img.format
    file_meta["pil_mode"] = img.mode
    file_meta["dimensions"] = f"{img.width} × {img.height} px"
    console.print(f"   Format: [cyan]{img.format}[/cyan]  Mode: [cyan]{img.mode}[/cyan]  "
                  f"Dimensions: [cyan]{img.width}×{img.height}[/cyan]\n")

    # ── EXIF ──────────────────────────────────────────────────────────────────
    exif = _extract_exif_raw(img)

    if not exif:
        console.print("   [dim]No EXIF data found in this file.[/dim]\n")
        return {"filepath": filepath, "file_meta": file_meta, "exif": {}, "gps_info": None}

    console.print(f"[bold]EXIF Highlights[/bold]  ({len(exif)} tags total)")
    _print_highlight_table(exif)

    # ── GPS ───────────────────────────────────────────────────────────────────
    gps_raw = exif.get("GPSInfo")
    gps_info = None
    if gps_raw:
        gps_info = _parse_gps(gps_raw)
        if gps_info:
            lat = gps_info.get("DecimalLatitude")
            lon = gps_info.get("DecimalLongitude")
            maps_link = gps_info.get("GoogleMapsLink", "")
            console.print(Panel(
                f"[bold red]⚠ GPS Data Found![/bold red]\n\n"
                f"  Latitude  : [green]{lat}[/green]\n"
                f"  Longitude : [green]{lon}[/green]\n"
                f"  Maps      : [link={maps_link}][cyan]{maps_link}[/cyan][/link]",
                title="[bold red]GPS Location[/bold red]",
                border_style="red",
            ))

    console.print(f"   [dim]Total EXIF tags extracted: {len(exif)}[/dim]\n")
    img.close()

    return {
        "filepath": filepath,
        "file_meta": file_meta,
        "exif": {k: str(v)[:200] for k, v in exif.items()},
        "gps_info": gps_info,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_metadata.py <path-to-image>")
        raise SystemExit(1)
    run(sys.argv[1])
