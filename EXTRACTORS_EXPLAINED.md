# 🔍 Extractors Explained — OLD vs NEW

## 📸 EXISTING: Image Metadata Extractor (`image_metadata.py`)

### How It Works (Step-by-Step)

```
STEP 1: USER PROVIDES LOCAL FILE
│
├─ Input: /Users/john/Downloads/photo.jpg
│
├─ Why local? 
│  • File system has full access to bytes
│  • Can read complete binary data
│  • No download/streaming issues
│

STEP 2: OPEN WITH PILLOW
│
├─ from PIL import Image
│ img = Image.open("photo.jpg")
│
├─ Pillow loads entire file into memory
│ • Reads JPEG headers
│ • Parses IFD (Image File Directory)
│ • Finds EXIF sub-directory
│

STEP 3: EXTRACT RAW EXIF DATA
│
├─ exif_raw = img._getexif()
│
├─ Returns dictionary:
│  {
│    271: "Apple",                          # Make (camera brand)
│    272: "iPhone 14 Pro",                  # Model
│    306: "2024:06:15 14:43:15",            # DateTime
│    34853: {GPS_IFD_dict},                 # GPS sub-directory
│    37500: b"binary_comment_data"          # UserComment
│  }
│
├─ Each number is a "tag ID"
│ • 271 = Make
│ • 272 = Model  
│ • 306 = DateTime
│ • 34853 = GPS info
│

STEP 4: MAP TAG IDs TO HUMAN NAMES
│
├─ from PIL.ExifTags import TAGS
│
├─ TAGS = {
│    271: "Make",
│    272: "Model",
│    306: "DateTime",
│    34853: "GPSInfo",
│    ...
│  }
│
├─ Convert: 271 → "Make"
│ Now we know tag 271 = camera brand
│

STEP 5: SPECIAL GPS PARSING
│
├─ GPS is stored in DMS format:
│  DMS = Degrees, Minutes, Seconds
│
├─ Raw data: (37, 1), (46, 1), (21.6, 10)
│
├─ These are fractions: 37/1, 46/1, 21.6/10
│ • 37°
│ • 46' (minutes)
│ • 21.6" (seconds)
│
├─ Convert to decimal:
│  37 + 46÷60 + 21.6÷3600 = 37.7727°N
│  122 + 25÷60 + 8.9÷3600 = 122.4191°W
│
├─ Result: 37.7727°N, 122.4191°W (exact coordinates!)
│

STEP 6: DISPLAY READABLE RESULTS
│
├─ Camera Make: Apple
│ Camera Model: iPhone 14 Pro
│ Capture Date: 2024-06-15 14:43:15
│ GPS: 37.7727°N, 122.4191°W
│ Google Maps: https://maps.google.com/?q=37.7727,122.4191
│

STEP 7: CLEAN UP
│
└─ img.close()  # Release file handle
```

### What It FINDS

✅ Camera make & model
✅ Lens model
✅ Focal length
✅ Aperture (F-number)
✅ ISO speed
✅ Shutter speed
✅ Capture date & time
✅ GPS coordinates (exact location!)
✅ Altitude
✅ Orientation
✅ Flash status
✅ White balance
✅ Software used
✅ Copyright info
✅ Artist name

### Limitations ❌

- ❌ Only works on **LOCAL files** (not URLs)
- ❌ Requires you to **download** the file first
- ❌ Doesn't extract **caption, comments, hashtags**
- ❌ Can't analyze **timeline or patterns**
- ❌ Can't link to **other posts by same person**
- ❌ No **privacy scoring**

### Example Output

```
FILE INFO
┌────────────┬──────────────────────┐
│ Filename   │ vacation_photo.jpg   │
│ Size       │ 2.3 MB               │
│ Dimensions │ 4032 × 3024 px       │
│ Format     │ JPEG                 │
└────────────┴──────────────────────┘

EXIF HIGHLIGHTS
┌──────────────────┬────────────────────────┐
│ Camera Make      │ Canon                  │
│ Camera Model     │ Canon EOS 5D Mark IV   │
│ Lens Model       │ Canon EF 24-70mm f/2.8│
│ Capture Date     │ 2024-06-15 14:43:15    │
│ GPS Coordinates  │ 37.7727°N, 122.4191°W │
│ Google Maps      │ https://maps.google... │
│ Focal Length     │ 35 mm                  │
│ F-Number         │ 2.8                    │
│ ISO Speed        │ 400                    │
│ Exposure Time    │ 1/100 sec              │
└──────────────────┴────────────────────────┘

🚨 GPS LOCATION DETECTED
   Exact Location: 37.7727°N, 122.4191°W
   Click to view: https://maps.google.com/?q=37.7727,122.4191
```

---

## 🔗 NEW: URL Post Extractor (`url_post_extractor.py`)

### How It Works (Step-by-Step)

```
STEP 1: USER PROVIDES SOCIAL MEDIA URL
│
├─ Input: https://instagram.com/p/CX9k4lJAb2K/
│
├─ NO DOWNLOAD NEEDED!
│ • Paste URL directly
│ • Tool handles fetching
│ • Instant extraction
│

STEP 2: DETECT PLATFORM
│
├─ Analyze URL pattern:
│  if "instagram.com" → Platform = Instagram
│  if "twitter.com" → Platform = Twitter/X
│  if "tiktok.com" → Platform = TikTok
│  if "youtube.com" → Platform = YouTube
│
├─ Different platforms need different parsers
│

STEP 3: FETCH POST WEBPAGE
│
├─ r = requests.get(url, headers=HEADERS)
│
├─ Downloads the HTML of the post
│ • Instagram page contains embedded JSON
│ • Twitter page has og: meta tags
│ • TikTok page has video metadata
│

STEP 4: EXTRACT META TAGS (og: tags)
│
├─ <meta property="og:title" content="...">
│ <meta property="og:description" content="...">
│ <meta property="og:image" content="https://...">
│ <meta property="og:url" content="https://...">
│
├─ These tags are visible in page source
│ • No authentication needed
│ • Public data
│

STEP 5: PARSE HTML WITH BeautifulSoup
│
├─ soup = BeautifulSoup(html, "html.parser")
│
├─ Find all visible content:
│  ✓ Post caption text
│  ✓ Author name
│  ✓ Comment count
│  ✓ Likes count
│  ✓ Post timestamp
│  ✓ Location tag
│  ✓ Image URLs
│

STEP 6: EXTRACT HASHTAGS & MENTIONS
│
├─ Regex pattern: #(\w+)
│ • Finds: #TechConf2024, #SanFrancisco, #AI
│
├─ Regex pattern: @(\w+)
│ • Finds: @john_doe, @jane_smith
│

STEP 7: DOWNLOAD IMAGE FROM URL
│
├─ For each image in post:
│  url = "https://cdn-images.instagram.com/..."
│  r = requests.get(url)
│  # Now we have the image bytes
│

STEP 8: EXTRACT EXIF FROM DOWNLOADED IMAGE
│
├─ REUSE existing image_metadata.py logic!
│
├─ Same process as local image:
│  • Load with Pillow
│  • Get _getexif()
│  • Parse GPS coordinates
│  • Extract camera info
│  • Convert GPS to decimal
│

STEP 9: GEOLOCATION INFERENCE
│
├─ From GPS coordinates:
│  37.7727°N, 122.4191°W
│
├─ Reverse geocode to:
│  "San Francisco Convention Center"
│  "747 Howard St, San Francisco, CA 94103"
│

STEP 10: TIMEZONE INFERENCE
│
├─ From post timestamp: 2024-06-15 14:43:15 UTC-7
│
├─ Deduce:
│  • Timezone: Pacific Time (UTC-7)
│  • Region: US West Coast
│  • Time zone: San Francisco area
│

STEP 11: ANALYZE COMMENTS
│
├─ Fetch all visible comments:
│  "Amazing view! Where is this?"
│  "@author It's at the Marriott!"
│
├─ Extract clues:
│  • Hotel name revealed
│  • More location data
│  • Other users' responses
│

STEP 12: CALCULATE PRIVACY RISK SCORE
│
├─ GPS data exposed?        +2.5 points
│  Location tagged?         +1.5 points
│  Comments visible?        +1.0 points
│  Timestamp posted?        +1.0 points
│  Hashtags reveal info?    +1.0 points
│  Social links?            +0.5 points
│                          ───────────
│  TOTAL: 8.5/10 (CRITICAL!)
│

STEP 13: GENERATE COMPREHENSIVE REPORT
│
├─ POST INFORMATION
│  ✓ Platform: Instagram
│  ✓ Author: @travel_blogger_x
│  ✓ Caption: "Amazing sunset in SF!"
│  ✓ Timestamp: 2024-06-15 14:43:15
│  ✓ Location: San Francisco Convention Center
│
├─ METADATA EXTRACTED
│  ✓ 3 images in carousel
│  ✓ 342 likes
│  ✓ 28 comments
│  ✓ Hashtags: #SanFrancisco #Travel #Sunset
│  ✓ Mentions: @friend1 @friend2
│
├─ IMAGE EXIF
│  ✓ Camera: iPhone 14 Pro
│  ✓ GPS: 37.7727°N, 122.4191°W (EXACT!)
│  ✓ Timestamp: 2024-06-15 14:43:15
│  ✓ Lens: iPhone main lens
│
├─ INFERENCES
│  ✓ Exact location: Convention Center
│  ✓ Exact time: 2:43 PM
│  ✓ Timezone: Pacific (UTC-7)
│  ✓ Activity: At an event
│  ✓ Travel pattern: In SF on this date
│
├─ VISIBLE COMMENTS (may contain clues)
│  ✓ "Where is this?" → Shows location interest
│  ✓ "See you at dinner!" → Plans revealed
│  ✓ "Room 512?" → Room number mentioned
│
└─ PRIVACY RISKS
   🔴 CRITICAL (8.5/10)
   Reason: Exact location + time + event = stalking data
```

### What It FINDS (More than just EXIF!)

✅ All EXIF data (from image)
✅ **Post caption text** (location hints!)
✅ **Author name** (link to profile)
✅ **Post timestamp** (activity pattern)
✅ **Location tag** (exact place)
✅ **Hashtags** (reveals interests/job)
✅ **@Mentions** (social connections)
✅ **Visible comments** (more data leaks!)
✅ **Number of likes/shares** (popularity/network)
✅ **Multiple images** (all analyzed)
✅ **Video duration** (TikTok/YouTube)
✅ **Privacy risk scoring** (tells you danger level)
✅ **Geolocation** (city from coordinates)
✅ **Recommendations** (how to stay safe)

### Advantages ✅

- ✅ **NO DOWNLOAD** — paste link, instant results
- ✅ **MORE DATA** — caption + comments + hashtags
- ✅ **MULTI-PLATFORM** — Instagram, Twitter, TikTok, YouTube, etc.
- ✅ **REAL-TIME** — gets current data
- ✅ **PRIVACY SCORE** — shows how exposed you are
- ✅ **RECOMMENDATIONS** — how to fix privacy
- ✅ **LINKED ACCOUNTS** — can find other posts by same person
- ✅ **TIMELINE BUILDING** — activity patterns

### Example Output

```
🔗 URL POST EXTRACTOR

Platform detected: Instagram

📋 POST INFORMATION
┌─────────────────┬───────────────────────────┐
│ Platform        │ Instagram                 │
│ URL             │ https://instagram.com/... │
│ Author          │ @travel_blogger_x        │
│ Timestamp       │ 2024-06-15 14:43:15       │
│ Location Tag    │ San Francisco             │
└─────────────────┴───────────────────────────┘

📝 CAPTION
   "Just arrived in SF for #TechConf2024! 
    Best city ever 🌉 @hotel_sf was amazing!"

🏷️ HASHTAGS & MENTIONS
   Hashtags: #TechConf2024, #SanFrancisco, #Travel
   Mentions: @hotel_sf, @john_doe

📸 EXIF METADATA
┌──────────────────┬──────────────────────┐
│ Make             │ Apple                │
│ Model            │ iPhone 14 Pro        │
│ DateTime         │ 2024-06-15 14:43:15  │
│ GPS_Location     │ 37.7727°N 122.4191°W │
└──────────────────┴──────────────────────┘

⚠️ GPS LOCATION EXPOSED
   https://maps.google.com/?q=37.7727,122.4191

🚨 PRIVACY RISK: 8.5/10

Exposed data:
   ✓ Exact GPS coordinates (street level)
   ✓ Exact timestamp
   ✓ Hotel name revealed
   ✓ Conference attendance
   ✓ Social network (tagged friends)

Can Be Used For:
   ✓ Know your exact location at specific time
   ✓ Find you at that location
   ✓ Know where you stayed
   ✓ Stalk other attendees
   ✓ Correlate with other posts

Recommendations:
   1. Disable location tagging
   2. Post photos AFTER event
   3. Remove EXIF before uploading
   4. Use private account
   5. Don't tag specific hotels
```

---

## 🆚 COMPARISON TABLE

| Feature | Image Metadata | URL Post Extractor |
|---------|---------------|--------------------|
| **Input** | Local file path | Social media URL |
| **Download needed** | YES ❌ | NO ✅ |
| **EXIF extraction** | ✅ YES | ✅ YES |
| **Caption/text** | ❌ NO | ✅ YES |
| **Comments analysis** | ❌ NO | ✅ YES |
| **Hashtags** | ❌ NO | ✅ YES |
| **Location tag** | ❌ NO | ✅ YES |
| **Author info** | ❌ NO | ✅ YES |
| **Mentions** | ❌ NO | ✅ YES |
| **Privacy scoring** | ❌ NO | ✅ YES |
| **Multi-platform** | ❌ Local only | ✅ 5+ platforms |
| **Real-time data** | N/A | ✅ Live |
| **Speed** | Medium (download) | Fast (URL fetch) |
| **Use case** | Found a photo | Found a post about you |

---

## 🎯 WHEN TO USE WHICH?

### Use Image Metadata When:
```
✓ You have a photo file
✓ You want EXIF details only
✓ Camera/lens info matters
✓ You're analyzing old photos
```

### Use URL Post Extractor When:
```
✓ Someone posted about you on Instagram/Twitter/TikTok
✓ You want EVERYTHING exposed (not just EXIF)
✓ You need privacy risk assessment
✓ You want to see what comments reveal
✓ You need to know if hashtags expose you
✓ You want privacy recommendations
```

---

## 💡 REAL EXAMPLE

### Scenario: Your Friend Posted a Photo of You

**Step 1: Find the post**
```
https://instagram.com/p/CX9k4lJAb2K/
```

**Step 2: OLD WAY (Image Metadata)**
```
1. Go to Instagram
2. Download the image (~3-5 MB)
3. Open EXIF viewer
4. See: Camera model, GPS, timestamp
5. Done
   
Time: ~5 minutes
Data: Only EXIF
```

**Step 3: NEW WAY (URL Post Extractor)**
```
1. Copy Instagram link
2. Paste in tool
3. Tool automatically:
   ✓ Fetches the page
   ✓ Extracts caption
   ✓ Gets comments
   ✓ Downloads image
   ✓ Extracts EXIF
   ✓ Finds hashtags
   ✓ Lists mentions
   ✓ Scores privacy risk
   ✓ Shows recommendations

Time: <10 seconds
Data: EVERYTHING (EXIF + metadata + comments + risk score)
```

---

## 🔒 Why This Matters

**Your existing Image Metadata extractor** shows:
> "This photo was taken with an iPhone at coordinates 37.77, 122.41"

**The new URL Post Extractor adds:**
> "This photo was posted at 2:43 PM on June 15 with caption 'At #TechConf2024' and your friend tagged you. Comments mention 'See you at the Marriott!' so anyone can find you at that specific hotel at that specific time."

**Difference:** Location alone vs. Location + Time + Event + Hotel + Social Network

---

## 📊 Menu Now Has

```
[1] Username Investigator         (20+ sites)
[2] Domain Intelligence            (DNS, SSL, WHOIS)
[3] Image Metadata Analyzer        (Local EXIF) ← OLD
[4] Keyword Tracker                (5 APIs)
[5] Email Investigator             (HIBP breaches)
[6] IP Address Tracker             (Geolocation)
[7] Phone Number Lookup            (Carrier)
[8] Website Scraper                (Links, emails)
[9] URL Post Extractor             (Instagram/Twitter) ← NEW!
[10] Generate Full Report          (TXT + HTML + CSV)
```

**Total: 10 modules + Report Generator**

---

## 🚀 Ready to Use!

```bash
python main.py
# Select option [9]
# Paste Instagram/Twitter URL
# Watch magic happen!
```
