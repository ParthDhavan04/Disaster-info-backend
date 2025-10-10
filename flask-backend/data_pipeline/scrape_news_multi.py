"""
scrape_news_multi.py
--------------------
Scrapes disaster articles from multiple Indian and international news sites (topic/search pages).
Max rows, max variety, ready for model training.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

MAX_PAGES = 8

NEWS_SOURCES = {
    "NDTV": {
        "base": "https://www.ndtv.com/topic/{}/page-{}",
    },
    "TOI": {
        "base": "https://timesofindia.indiatimes.com/topic/{}/{}",
    },
    "IndianExpress": {
        "base": "https://indianexpress.com/about/{}/page/{}",
    },
    "HindustanTimes": {
        "base": "https://www.hindustantimes.com/topic/{}/page-{}",
    },
    "BBC": {
        "base": "https://www.bbc.co.uk/search?q={}&page={}",
    }
}

DISASTER_LABELS = ["flood", "earthquake", "fire", "cyclone", "landslide"]

def extract_ndtv(url, label, source):
    try:
        r = requests.get(url, timeout=10)
        s = BeautifulSoup(r.text, "html.parser")
        articles = []
        for item in s.select(".news_Listing .news_Listing_content"):
            h = item.find("a", {"class": "newsHdng"})
            p = item.find("p", {"class": "newsCont"})
            headline = h.get_text(strip=True) if h else ''
            summary = p.get_text(strip=True) if p else ''
            if headline and len(headline.split()) > 3:
                articles.append({"text": headline + " " + summary, "label": label, "source": source})
        return articles
    except Exception as e:
        print("[NDTV]", e)
        return []

def extract_toi(url, label, source):
    try:
        r = requests.get(url, timeout=10)
        s = BeautifulSoup(r.text, "html.parser")
        articles = []
        for block in s.select(".content li"):
            h = block.find("span", {"class": "w_tle"})
            p = block.find("div", {"class": "synopsis"})
            headline = h.get_text(strip=True) if h else ''
            summary = p.get_text(strip=True) if p else ''
            if headline and len(headline.split()) > 3:
                articles.append({"text": headline + " " + summary, "label": label, "source": source})
        return articles
    except Exception as e:
        print("[TOI]", e)
        return []

def extract_indianexpress(url, label, source):
    try:
        r = requests.get(url, timeout=10)
        s = BeautifulSoup(r.text, "html.parser")
        articles = []
        for item in s.select(".result-content"):
            h = item.find("a")
            headline = h.get_text(strip=True) if h else ''
            if headline and len(headline.split()) > 3:
                articles.append({"text": headline, "label": label, "source": source})
        return articles
    except Exception as e:
        print("[IndianExpress]", e)
        return []

def extract_ht(url, label, source):
    try:
        r = requests.get(url, timeout=10)
        s = BeautifulSoup(r.text, "html.parser")
        articles = []
        for card in s.select(".media"):
            h = card.find("div", {"class": "media-body"})
            if h:
                headline = h.find("a")
                para = h.find("div", {"class": "para-txt"})
                t = (headline.get_text(strip=True) if headline else '') + " " + (para.get_text(strip=True) if para else '')
                if t and len(t.split()) > 3:
                    articles.append({"text": t, "label": label, "source": source})
        return articles
    except Exception as e:
        print("[HT]", e)
        return []

def extract_bbc(url, label, source):
    try:
        r = requests.get(url, timeout=10)
        s = BeautifulSoup(r.text, "html.parser")
        articles = []
        for item in s.select("article"):
            h = item.find("h1") or item.find("h2") or item.find("a")
            if h:
                t = h.get_text(strip=True)
                if t and len(t.split()) > 3:
                    articles.append({"text": t, "label": label, "source": source})
        return articles
    except Exception as e:
        print("[BBC]", e)
        return []

scrapers = {
    "NDTV": extract_ndtv,
    "TOI": extract_toi,
    "IndianExpress": extract_indianexpress,
    "HindustanTimes": extract_ht,
    "BBC": extract_bbc
}

all_rows = []
print("[INFO] Scraping multiple news sources/pages with disaster topics...\n")

for source, info in NEWS_SOURCES.items():
    extract_fn = scrapers[source]
    for label in DISASTER_LABELS:
        base_url = info["base"]
        for page in tqdm(range(1, MAX_PAGES + 1), desc=f"{source}-{label}"):
            url = base_url.format(label, page)
            data = extract_fn(url, label, source)
            all_rows.extend(data)
            time.sleep(1.3)

df = pd.DataFrame(all_rows).drop_duplicates(subset=["text"])
df.to_csv("raw_news.csv", index=False, encoding="utf-8")

print(f"\n[SUCCESS] Scraped {len(df)} articles → raw_news.csv")
