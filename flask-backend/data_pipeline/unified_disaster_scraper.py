"""
unified_disaster_scraper.py
---------------------------
Fetches up to 20,000+ disaster-related events from dozens of RSS, global disaster feeds, and paged APIs.
Deduplicates and saves to disaster_huge_dataset.csv
"""

import pandas as pd
import feedparser
import time
import requests
from tqdm import tqdm
from html import unescape

# --- Configs ---
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

ALL_RSS_FEEDS = [
    # National and international
    "https://feeds.feedburner.com/ndtvnews-latest",
    "https://feeds.feedburner.com/NDTV-LatestNews",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://indianexpress.com/feed/",
    "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
    "https://www.oneindia.com/rss/news-india-fb.xml",
    "https://zeenews.india.com/rss/india-national-news.xml",
    "https://www.news18.com/rss/india.xml",
    # City/state topic feeds
    "https://timesofindia.indiatimes.com/rssfeeds/-2128838597.cms",  # Delhi
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",  # Mumbai
    "https://timesofindia.indiatimes.com/rssfeeds/-2128839821.cms",  # Bengaluru
    # Global/Asia
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "http://feeds.reuters.com/reuters/worldNews",
    "http://feeds.reuters.com/reuters/INtopNews",
    # Disaster-specific feeds
    "https://reliefweb.int/disasters/rss.xml",
    "https://reliefweb.int/updates/rss.xml",
    "https://reliefweb.int/reports/rss.xml",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.atom",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.atom",
    "https://mausam.imd.gov.in/rssfeed/forecast.xml",
    "https://www.gdacs.org/xml/rss_7d.xml",  # Global disaster alert system
    "https://floodlist.com/feed",  # FloodList
    "https://www.tribuneindia.com/rss/state"
    # Add more as needed
]

all_items = []

print("[INFO] Scraping ALL RSS/ATOM feeds...")
for url in tqdm(ALL_RSS_FEEDS):
    try:
        d = feedparser.parse(url)
        for entry in d.entries:
            title = unescape(entry.get("title", ""))
            summary = unescape(entry.get("summary", ""))
            desc = unescape(entry.get("description", ""))
            text = f"{title} {summary} {desc}".strip()
            text = text.replace("\xa0", " ").replace("\n", " ")
            if text and len(text.split()) > 7:
                label = match_disaster(text)
                # Only keep meaningful disasters (or keep all with their label)
                if label != "other":
                    all_items.append({
                        "text": text,
                        "label": label,
                        "source": url.split('/')[2]
                    })
        time.sleep(0.5)
    except Exception as e:
        print(f"[ERROR] {url}: {e}")

# Max out ReliefWeb's API (200 × 25 = 5,000 rows) and even more for historic data
print("[INFO] Scraping ReliefWeb paged API...")
for page in tqdm(range(1, 30)):
    url = f"https://api.reliefweb.int/v1/disasters?appname=scraper&limit=200&page={page}"
    try:
        r = requests.get(url, timeout=15)
        for disaster in r.json().get("data", []):
            fields = disaster.get("fields", {})
            name = unescape(fields.get("name", ""))
            description = unescape(fields.get("description", ""))
            text = f"{name} {description}".strip()
            if text and len(text.split()) > 7:
                label = match_disaster(text)
                if label != "other":
                    all_items.append({
                        "text": text,
                        "label": label,
                        "source": "reliefweb"
                    })
        time.sleep(0.35)
    except Exception as e:
        print(f"[ERROR] ReliefWeb: {e}")

# Fetch from USGS over multiple feeds: month/year, significant/4.5+
print("[INFO] Scraping USGS multi-feed historic API...")
usgs_keys = ["significant_month", "significant_year", "4.5_month", "4.5_year"]
for key in tqdm(usgs_keys):
    url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{key}.geojson"
    try:
        r = requests.get(url, timeout=15)
        for feat in r.json().get("features", []):
            props = feat["properties"]
            title = unescape(props.get("title", ""))
            place = unescape(props.get("place", ""))
            text = f"{title} at {place}".strip()
            if text and len(text.split()) > 7:
                all_items.append({
                    "text": text,
                    "label": "earthquake",
                    "source": "usgs"
                })
        time.sleep(0.35)
    except Exception as e:
        print(f"[ERROR] USGS: {e}")

df = pd.DataFrame(all_items).drop_duplicates(subset=["text"])
df = df[df['label'] != 'other']
df.to_csv("disaster_huge_dataset.csv", index=False, encoding="utf-8")
print(f"\n[SUCCESS] Scraped {len(df)} disaster events → disaster_huge_dataset.csv")
print(df["label"].value_counts())
