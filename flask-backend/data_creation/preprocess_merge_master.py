import pandas as pd
import uuid
import re
import glob
import os

# --- File paths / directories ---
KAGGLE_PATH = "raw/train.csv"
CRISISLEX_DIR = "raw/crisislex_t26/"  # directory containing event subfolders
DISASTER_MESSAGES_PATH = "raw/disaster_messages.csv"
INDIA_EVENTS_PATH = "raw/natural_disasters_india.csv"
OWN_SCRAPES_PATH = "raw/disaster_huge_dataset.csv"
RAW_NEWS_PATH = "raw/one_raw_news.csv"

# --- Helper functions ---
def clean_txt(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def map_label(label: str) -> str:
    lbl = str(label).lower()
    if "flood" in lbl:
        return "flood"
    if "earthquake" in lbl or "quake" in lbl or "seismic" in lbl:
        return "earthquake"
    if "fire" in lbl or "blaze" in lbl or "wildfire" in lbl:
        return "fire"
    if "cyclone" in lbl or "typhoon" in lbl or "hurricane" in lbl or "storm" in lbl:
        return "cyclone"
    if "landslide" in lbl or "mudslide" in lbl or "rockslide" in lbl:
        return "landslide"
    return "other"

# --- Kaggle Disaster Tweets ---
df_kaggle = pd.read_csv(KAGGLE_PATH)
df_kaggle_real = df_kaggle[df_kaggle["target"] == 1].copy()
df_kaggle_real["id"] = df_kaggle_real["id"].apply(str)
df_kaggle_real["source"] = "twitter"
df_kaggle_real["raw_text"] = df_kaggle_real["text"]
df_kaggle_real["clean_text"] = df_kaggle_real["text"].apply(clean_txt)
df_kaggle_real["disaster_label"] = df_kaggle_real["keyword"].apply(map_label)
df_kaggle_real["severity_label"] = ""
df_kaggle_real["location_text"] = df_kaggle_real["location"].fillna("")
df_kaggle_real["timestamp"] = ""
df_kaggle_real["lat"] = ""
df_kaggle_real["lon"] = ""
df_kaggle_real["media_urls"] = ""
df_kaggle_real["engagement"] = ""
df_kaggle_real["validated"] = False
df_kaggle_real = df_kaggle_real[["id","source","timestamp","raw_text","clean_text","disaster_label","severity_label","location_text","lat","lon","media_urls","engagement","validated"]]

# --- CrisisLex (recursive folder scan) ---
def process_crisislex_folder(base_dir):
    dfs = []
    for filename in glob.glob(os.path.join(base_dir, "**/*.csv"), recursive=True):
        try:
            df = pd.read_csv(filename, encoding="utf-8")
            df["id"] = df["tweet_id"].astype(str)
            df["source"] = "twitter"
            df["raw_text"] = df["text"]
            df["clean_text"] = df["text"].apply(clean_txt)
            if "topic" in df.columns:
                df["disaster_label"] = df["topic"].apply(map_label)
            else:
                event_label = os.path.basename(filename).split("_")[1] if "_" in os.path.basename(filename) else os.path.basename(os.path.dirname(filename))
                df["disaster_label"] = map_label(event_label)
            df["severity_label"] = ""
            df["location_text"] = ""
            df["timestamp"] = ""
            df["lat"] = ""
            df["lon"] = ""
            df["media_urls"] = ""
            df["engagement"] = ""
            df["validated"] = False
            df = df[["id","source","timestamp","raw_text","clean_text","disaster_label","severity_label",
                     "location_text","lat","lon","media_urls","engagement","validated"]]
            dfs.append(df)
        except Exception as e:
            print(f"[ERROR] {filename}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=["id","source","timestamp","raw_text","clean_text","disaster_label","severity_label",
                     "location_text","lat","lon","media_urls","engagement","validated"])
df_crisis = process_crisislex_folder(CRISISLEX_DIR)

# --- Disaster Messages Dataset (formerly Disaster Response Messages) ---
df_msg = pd.read_csv(DISASTER_MESSAGES_PATH)
df_msg["id"] = df_msg.index.map(lambda i: f"msg_{i}")
df_msg["source"] = "other"
df_msg["raw_text"] = df_msg["message"]
df_msg["clean_text"] = df_msg["message"].apply(clean_txt)
df_msg["disaster_label"] = df_msg["genre"].apply(map_label) if "genre" in df_msg.columns else "other"
df_msg["severity_label"] = ""
df_msg["location_text"] = ""
df_msg["timestamp"] = ""
df_msg["lat"] = ""
df_msg["lon"] = ""
df_msg["media_urls"] = ""
df_msg["engagement"] = ""
df_msg["validated"] = False
df_msg = df_msg[["id","source","timestamp","raw_text","clean_text","disaster_label","severity_label","location_text","lat","lon","media_urls","engagement","validated"]]


df_india = pd.read_csv(INDIA_EVENTS_PATH)
df_india["id"] = df_india.index.map(lambda i: f"india_{i}")
df_india["source"] = "wiki"
df_india["raw_text"] = df_india["Disaster_Info"].astype(str)
df_india["clean_text"] = df_india["raw_text"].apply(clean_txt)
df_india["disaster_label"] = df_india["Title"].apply(map_label)
df_india["severity_label"] = ""
df_india["location_text"] = df_india["Title"].astype(str)
df_india["timestamp"] = df_india["Date"].astype(str) if "Date" in df_india.columns else df_india["Year"].astype(str)
df_india["lat"] = ""
df_india["lon"] = ""
df_india["media_urls"] = ""
df_india["engagement"] = ""
df_india["validated"] = False
df_india = df_india[["id","source","timestamp","raw_text","clean_text","disaster_label","severity_label",
                     "location_text","lat","lon","media_urls","engagement","validated"]]


# --- Own Scrapes ---
df_own = pd.read_csv(OWN_SCRAPES_PATH)
def default_clean_row(row):
    return pd.Series({
        "id": str(uuid.uuid4()),
        "source": row.get("source", ""),
        "timestamp": "",
        "raw_text": row["text"],
        "clean_text": clean_txt(row["text"]),
        "disaster_label": map_label(row.get("label", "")),
        "severity_label": "",
        "location_text": "",
        "lat": "",
        "lon": "",
        "media_urls": "",
        "engagement": "",
        "validated": False
    })
df_own_clean = df_own.apply(default_clean_row, axis=1)

# --- one_raw_news.csv ---
df_news = pd.read_csv(RAW_NEWS_PATH)
def process_news_row(row):
    return pd.Series({
        "id": str(uuid.uuid4()),
        "source": row.get("source", ""),
        "timestamp": "",
        "raw_text": row.get("text", ""),
        "clean_text": clean_txt(row.get("text", "")),
        "disaster_label": map_label(row.get("label", "")),
        "severity_label": "",
        "location_text": "",
        "lat": "",
        "lon": "",
        "media_urls": "",
        "engagement": "",
        "validated": False
    })
df_news_clean = df_news.apply(process_news_row, axis=1)

# --- Merge all, deduplicate, and save ---
dfs_to_merge = [df_kaggle_real, df_crisis, df_msg, df_india, df_own_clean, df_news_clean]
df_master = pd.concat(dfs_to_merge, ignore_index=True)
df_master.drop_duplicates(subset=["clean_text"], inplace=True)
df_master.to_csv("disaster_master_dataset.csv", index=False, encoding="utf-8")
print(f"Final shape: {df_master.shape}")
print(df_master["disaster_label"].value_counts())
