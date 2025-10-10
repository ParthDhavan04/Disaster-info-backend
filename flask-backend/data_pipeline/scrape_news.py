"""
scrape_news.py (paginated)
--------------------------
Scrapes multiple pages of disaster-related articles from news sites.
Generates 5K–10K rows easily.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

MAX_PAGES = 10  # scrape up to 10 pages per topic

NEWS_SOURCES = {
    "NDTV": {
        "flood": "https://www.ndtv.com/topic/flood/page-{}",
        "earthquake": "https://www.ndtv.com/topic/earthquake/page-{}",
        "fire": "https://www.ndtv.com/topic/fire/page-{}",
        "cyclone": "https://www.ndtv.com/topic/cyclone/page-{}",
        "landslide": "https://www.ndtv.com/topic/landslide/page-{}"
    },
    "TOI": {
        "flood": "https://timesofindia.indiatimes.com/topic/flood/{}",
        "earthquake": "https://timesofindia.indiatimes.com/topic/earthquake/{}",
        "fire": "https://timesofindia.indiatimes.com/topic/fire/{}",
        "cyclone": "https://timesofindia.indiatimes.com/topic/cyclone/{}",
        "landslide": "https://timesofindia.indiatimes.com/topic/landslide/{}"
    },
}

def extract_texts(url, label, source):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        texts = []
        for tag in soup.find_all(["a", "h2", "p"]):
            text = tag.get_text(strip=True)
            if text and len(text.split()) > 6:
                texts.append(text)
        return [{"text": t, "label": label, "source": source} for t in texts]
    except Exception as e:
        print(f"[ERROR] {source}-{label}: {e}")
        return []


all_rows = []
print("[INFO] Starting paginated news scraping...\n")

for source, topics in NEWS_SOURCES.items():
    for label, base_url in topics.items():
        for page in tqdm(range(1, MAX_PAGES + 1), desc=f"{source}-{label}"):
            url = base_url.format(page)
            data = extract_texts(url, label, source)
            all_rows.extend(data)
            time.sleep(1.0)

df = pd.DataFrame(all_rows).drop_duplicates(subset=["text"])
df.to_csv("raw_news.csv", index=False, encoding="utf-8")

print(f"\n[SUCCESS] Scraped {len(df)} articles → raw_news.csv")
