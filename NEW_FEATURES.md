# 🔥 Aadi OSINT Toolkit — EXTENDED VERSION

## What's New (4 Modules + 2 Features)

### ✅ 4 NEW MODULES

#### 1. 📧 Email Investigator (`email_investigator.py`)
- **What it does:** Checks if an email has been exposed in public data breaches
- **Data sources:**
  - Have I Been Pwned (HIBP) API — Troy Hunt's free breach database
  - HIBP Pastes — checks if email appeared in leaked paste sites
  - Email format validation (RFC 5322)
- **Output:** 
  - Validation status
  - List of breaches (if any)
  - Paste site mentions
  - Days compromised
- **Use case:** Check your own email security, OSINT on email accounts

---

#### 2. 📍 IP Address Tracker (`ip_tracker.py`)
- **What it does:** Gathers geolocation, ISP, and network info on an IP
- **Data sources:**
  - ip-api.com (free tier, 45 req/min) — detailed GeoIP + ASN + hosting info
  - Automatic validation (IPv4/IPv6, private vs public)
- **Output:**
  - Country, Region, City
  - Coordinates (lat/lon) → Google Maps link
  - ISP name & organization
  - ASN (Autonomous System Number)
  - Flags: Mobile, Proxy/VPN, Data Center
- **Use case:** Identify server locations, detect CDNs, find suspicious hosting

---

#### 3. 📱 Phone Number Lookup (`phone_lookup.py`)
- **What it does:** Validates and analyses phone numbers internationally
- **Data sources:**
  - phonenumbers library (Google's open-source phone parser)
  - Public carrier databases
  - International format support (190+ countries)
- **Output:**
  - Validation (valid vs possible format)
  - Phone type (mobile, fixed-line, VoIP, etc.)
  - Carrier name
  - Timezone
  - Geographic area (city/region)
  - Formatting variations (E.164, International, National, RFC3966)
- **Use case:** Validate phone numbers, identify carrier/type, cross-reference with public profiles

---

#### 4. 🕸️ Website Scraper (`website_scraper.py`)
- **What it does:** Extracts metadata, links, and emails from any public website
- **Data sources:**
  - Live HTTP requests to the target URL
  - HTML parsing with BeautifulSoup4
  - Respects robots.txt spirit (no aggressive crawling)
- **Output:**
  - Page title, description, keywords
  - Open Graph metadata (og:title, og:image, og:description)
  - All links (internal/external categorized)
  - Email addresses (from mailto: links and visible text)
  - Meta tags inventory
  - Server & Content-Type headers
  - Technology hints (framework detection via meta tags)
- **Use case:** Gather open-source web intelligence, find contact emails, enumerate site structure

---

### ✨ 2 NEW FEATURES

#### Feature #1: 📊 CSV Export
- **Where:** Report Generator module
- **What it does:** Exports all collected data into a CSV spreadsheet
- **Columns:** Type, Target, Field, Category, Value, Status
- **Benefits:**
  - Easy to import into Excel/Google Sheets
  - Pivot tables for data analysis
  - Share with team members
  - Archive findings in standard format
- **Example row:**
  ```
  Email, attacker@example.com, Breach, Adobe, 2013-10-04, LEAKED
  ```

---

#### Feature #2: 🗺️ Visual HTML Map for GPS
- **Where:** Image Metadata module & Report Generator
- **What it does:** Displays GPS coordinates as an interactive map link
- **Integration:**
  - Image with GPS → shows Google Maps link automatically
  - Click to view exact location
  - Embedded in HTML report
- **Security note:** ⚠️ GPS in photos can dox people — handle responsibly!

---

## Updated Files Summary

| File | Status | What Changed |
|------|--------|--------------|
| `main.py` | 🔄 Updated | Added 4 new menu options (5-8), expanded session tracking |
| `report_generator.py` | 🔄 Updated | Added `_export_csv()` function, CSV export in reports |
| `email_investigator.py` | ✨ NEW | Email breach checking via HIBP |
| `ip_tracker.py` | ✨ NEW | IP geolocation & ISP lookup |
| `phone_lookup.py` | ✨ NEW | International phone validation |
| `website_scraper.py` | ✨ NEW | HTML metadata + link/email extraction |
| `requirements.txt` | 🔄 Updated | Added: beautifulsoup4, phonenumbers |

---

## How to Use the New Modules

### 📧 Email Investigator
```bash
# In menu, press: 5
# Enter: your.email@example.com
# Output: List of breaches (if any) or "Good news!"
```

### 📍 IP Tracker
```bash
# In menu, press: 6
# Enter: 8.8.8.8  (or any public IP)
# Output: Country, City, ISP, Coordinates
```

### 📱 Phone Lookup
```bash
# In menu, press: 7
# Enter: +1-202-555-0173  (any format works)
# Country: US  (or leave blank for US)
# Output: Carrier, Type, Timezone
```

### 🕸️ Website Scraper
```bash
# In menu, press: 8
# Enter: example.com  (with or without https://)
# Output: All links, emails, metadata found on page
```

### 📊 CSV Export
```bash
# After running modules, press: 9 (Generate Report)
# Output: osint_report_TIMESTAMP.csv in reports/ folder
# Open in Excel or Google Sheets
```

---

## New Dependencies

```bash
pip install beautifulsoup4 phonenumbers
```

Or just re-run:
```bash
pip install -r requirements.txt
```

---

## Menu Now Shows 11 Options

```
[1] Username Investigator     — 20+ public sites
[2] Domain Intelligence       — DNS, SSL, WHOIS
[3] Image Metadata            — EXIF, GPS
[4] Keyword Tracker           — HN, Reddit, GitHub, arXiv
[5] Email Investigator        — 🔴 NEW: HIBP breaches
[6] IP Tracker                — 🔴 NEW: Geolocation
[7] Phone Lookup              — 🔴 NEW: Carrier & validation
[8] Website Scraper           — 🔴 NEW: Links, emails, metadata
[9] Generate Full Report      — TXT + HTML + 🔴 CSV
[A] About / Help
[0] Exit
```

---

## Example Workflow

```
1. Run Username Investigator on "johndoe"
   → Finds presence on GitHub, Twitter, Reddit
   
2. Run Email Investigator on "john@company.com"
   → Shows if email was in LinkedIn breach (2012)
   
3. Run Website Scraper on "company.com"
   → Extracts 50+ links, finds 3 contact emails
   
4. Run IP Tracker on "203.0.113.42"
   → Shows it's hosted in AWS Dublin, Ireland
   
5. Generate Full Report
   → Creates osint_report_20250616_143022.txt/html/csv
   → Open CSV in Excel for pivot table analysis
```

---

## Total Modules: 8️⃣ + Report Generator

✅ All 100% legal, ethical OSINT only  
✅ No API keys required  
✅ Public data sources  
✅ Educational purpose  

**Happy investigating! 🔍**
