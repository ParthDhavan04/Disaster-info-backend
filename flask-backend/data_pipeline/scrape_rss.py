"""
scrape_disaster_rss.py
----------------------
Fetches from disaster-specific RSS feeds and APIs for maximum disaster content.
"""

import feedparser
import pandas as pd
from tqdm import tqdm
import time
import requests

DISASTER_KEYWORDS = {
    "flood": ["flood", "flooding", "waterlogged", "inundated", "deluge", "overflow"],
    "earthquake": ["earthquake", "quake", "tremor", "seismic", "aftershock"],
    "fire": ["fire", "blaze", "wildfire", "forest fire", "burning", "flames"],
    "cyclone": ["cyclone", "hurricane", "typhoon", "storm", "landfall"],
    "landslide": ["landslide", "mudslide", "rockslide", "hill collapse", "slope failure"],
    "other": ["disaster", "emergency", "rescue", "evacuation", "collapse", "explosion"]
}

def match_disaster(text):
    t = text.lower()
    for label, keywords in DISASTER_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return label
    return "other"

# DISASTER-FOCUSED RSS FEEDS AND APIs
DISASTER_SOURCES = [
    # ReliefWeb - Global disaster database
    "https://reliefweb.int/disasters/rss.xml",
    "https://reliefweb.int/updates/rss.xml",
    "https://reliefweb.int/reports/rss.xml",
    
    # USGS Earthquake feeds
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.atom",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.atom",
    
    # Weather/Climate disaster feeds
    "https://www.nhc.noaa.gov/xml/",  # Hurricane center
    "https://alerts.weather.gov/cap/us.php?x=0",  # Weather alerts
    
    # Indian disaster sources
    "https://ndma.gov.in/en/media-public-awareness/rss.xml",
    "https://mausam.imd.gov.in/rssfeed/forecast.xml",
    
    # Global disaster monitoring
    "https://www.gdacs.org/xml/rss_7d.xml",  # Global Disaster Alert System
    "https://floodlist.com/feed",  # FloodList - flood news
    
    # News sources filtered for disaster keywords (regional)
    "https://www.tribuneindia.com/rss/state",
    "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",
]

all_items = []

print("[INFO] Fetching from disaster-specific sources...")

# RSS Feeds
for url in tqdm(DISASTER_SOURCES):
    try:
        d = feedparser.parse(url)
        for entry in d.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            desc = entry.get("description", "")
            
            text = f"{title} {summary} {desc}".strip()
            
            if text and len(text.split()) > 5:
                label = match_disaster(text)
                # Only keep if it matches disaster keywords
                if label != "other":
                    all_items.append({
                        "text": text,
                        "label": label,
                        "source": url.split('/')[2]  # Extract domain
                    })
        time.sleep(1)
    except Exception as e:
        print(f"[ERROR] {url}: {e}")

# ReliefWeb API for more disaster data
try:
    print("Fetching ReliefWeb disasters...")
    for page in range(1, 6):
        url = f"https://api.reliefweb.int/v1/disasters?appname=scraper&limit=200&page={page}"
        r = requests.get(url, timeout=15)
        data = r.json().get("data", [])
        
        for disaster in data:
            fields = disaster.get("fields", {})
            name = fields.get("name", "")
            description = fields.get("description", "")
            
            text = f"{name} {description}".strip()
            if text and len(text.split()) > 5:
                label = match_disaster(text)
                all_items.append({
                    "text": text,
                    "label": label,
                    "source": "reliefweb"
                })
        time.sleep(0.5)
except Exception as e:
    print(f"[ERROR] ReliefWeb API: {e}")

# USGS Earthquakes (JSON API)
try:
    print("Fetching USGS earthquakes...")
    r = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson", timeout=10)
    data = r.json()
    
    for feature in data.get("features", []):
        props = feature["properties"]
        title = props.get("title", "")
        place = props.get("place", "")
        
        if title:
            text = f"{title} at {place}".strip()
            all_items.append({
                "text": text,
                "label": "earthquake",
                "source": "usgs"
            })
except Exception as e:
    print(f"[ERROR] USGS: {e}")

# Remove duplicates and save
df = pd.DataFrame(all_items).drop_duplicates(subset=["text"])
df = df[df['label'] != 'other']  # Filter out non-disaster content

df.to_csv("disaster_focused_data.csv", index=False, encoding="utf-8")
print(f"\n[SUCCESS] Scraped {len(df)} DISASTER articles → disaster_focused_data.csv")

# Show distribution
print("\nLabel distribution:")
print(df['label'].value_counts())
