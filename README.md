# 🔍 Aadi OSINT Toolkit
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow.svg)](https://www.python.org/)
[![Educational](https://img.shields.io/badge/Purpose-Educational-green.svg)](#)

```
  ____          ____  _____ _   _ _______   _______ ____   ____  _     _  _______ _______
 / __ \   /\   |  _ \|  __ \| \ | |_   _\ \ / / ____|  _ \ / __ \| |   | |/ /_   _|__   __|
| |  | | /  \  | |_) | |  | |  \| | | |  \ V /|  _| | |_) | |  | | |   | ' /  | |    | |
| |  | |/ /\ \ |  _ <| |  | | . ` | | |   > < | |___|  _ <| |  | | |   |  <   | |    | |
| |__| / ____ \| |_) | |__| | |\  |_| |_ / . \|_____|_| \_\ |__| | |___| . \ _| |_   | |
 \____/_/    \_\____/|_____/|_| \_|_____/_/ \_\______|_|   \_\____/|_____|_|\_\_____|  |_|
```

**A legal, ethical OSINT toolkit for cybersecurity learners.**  
100% public data only · No hacking · No exploitation · Educational use

---

## 📁 Project Structure

```
aadi_osint_toolkit/
│
├── main.py                  ← Entry point (interactive CLI menu)
├── username_checker.py      ← Username presence across public sites
├── domain_intel.py          ← DNS, SSL, WHOIS lookup
├── image_metadata.py        ← EXIF extraction from images
├── keyword_tracker.py       ← Public keyword search (HN, Reddit, GitHub, etc.)
├── report_generator.py      ← TXT + HTML report builder
├── email_investigator.py    ← Email investigator
├── ip_tracker.py            ← Tracks down IP
├── phone_lookup.py          ← Extracts publicly available data
├── website_scraper.py       ← Extracts available data on websites
├── url_post_extractor.py    ← Extracts posts from urls
│
├── sites_config.json        ← Customisable site list for username checking
├── requirements.txt         ← Python dependencies
├── README.md                ← This file
│
└── reports/                 ← Generated reports saved here (auto-created)
    ├── osint_report_YYYYMMDD_HHMMSS.txt
    └── osint_report_YYYYMMDD_HHMMSS.html
```

---

## ⚡ Quick Start

### 1. Clone / Download the project

```bash
git clone https://github.com/DrPhrma/aadi-osint-toolkit.git
cd aadi-osint-toolkit
```

Or just copy all the files into a folder called `aadi_osint_toolkit/`.

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the toolkit

```bash
python main.py
```

You'll see the ASCII banner and an interactive menu.

---

## 🧩 Module Details

### 👤 Username Investigator

- Enter a username (e.g. `johndoe`)
- The tool sends HTTP requests to all sites in `sites_config.json`
- A progress bar tracks the scan
- Results table shows: site name, category, HTTP status, URL
- **Customise sites:** edit `sites_config.json` — add any site with a `{username}` placeholder

### 🌐 Domain Intelligence

- Enter a domain (e.g. `example.com` or `https://example.com`)
- Fetches:
  - DNS records (A, AAAA, MX, TXT, NS, CNAME) via `dnspython`
  - SSL certificate details (subject, issuer, expiry, SANs, cipher) via `ssl`
  - WHOIS registration data (registrar, dates, org) via `python-whois`

### 🖼 Image Metadata Analyzer

- Enter a path to an image file (JPEG recommended — most EXIF data lives there)
- Extracts: camera make/model, capture date, software, GPS coordinates, lens, ISO, f-number
- **⚠ GPS Warning:** if GPS data is present, the tool shows the coordinates and a Google Maps link

### 🔎 Public Keyword Tracker

- Enter any keyword (e.g. `artificial intelligence`)
- Searches across 5 free public APIs simultaneously:
  - **HackerNews** — stories and comments (Algolia API)
  - **Wikipedia** — article search
  - **Reddit** — posts from r/all (public JSON API, no auth)
  - **GitHub** — public repositories
  - **arXiv** — academic papers
- Results displayed per source with titles and links

### 📄 Report Generator

- Combines all module results from the current session
- Generates:
  - `osint_report_TIMESTAMP.txt` — plain text, easy to read / archive
  - `osint_report_TIMESTAMP.html` — styled dark-theme HTML, open in any browser
- Reports saved to the `reports/` folder

---

## ⚙️ Configuration

### Adding custom sites to username checking

Edit `sites_config.json`:

```json
{
  "sites": [
    {
      "name": "MyCustomSite",
      "url": "https://mycustomsite.com/user/{username}",
      "category": "Social"
    }
  ]
}
```

The `{username}` placeholder is replaced with the target username at runtime.

---

## 🐍 Requirements

| Package | Purpose |
|---------|---------|
| `rich` | Beautiful terminal tables, panels, progress bars |
| `requests` | HTTP requests for username/keyword modules |
| `dnspython` | DNS record resolution |
| `Pillow` | EXIF image metadata extraction |
| `python-whois` | Domain WHOIS lookup (optional) |

Python **3.10+** required (uses `dict | None` union type hints).

---

## ⚠️ Legal & Ethical Use

This toolkit is designed for **educational cybersecurity learning only**.

- ✅ Only queries **publicly available** data
- ✅ Uses only **free, open APIs** — no API keys required
- ✅ Respects `robots.txt` spirit — no scraping at scale
- ❌ **Never** use for unauthorized surveillance
- ❌ **Never** use against individuals without proper legal authorization
- ❌ **Never** use to stalk, harass, or harm anyone

Always comply with:
- Your local laws and regulations
- The terms of service of websites you query
- Responsible disclosure principles

---

## 🎓 Learning Resources

- [OSINT Framework](https://osintframework.com/)
- [Bellingcat OSINT Guide](https://www.bellingcat.com/resources/how-tos/2021/11/09/a-beginners-guide-to-osint-investigation-with-maltego/)
- [SANS OSINT Curriculum](https://www.sans.org/blog/what-is-osint-how-is-it-used/)

---

*Built for learning. Handle intelligence responsibly.*
