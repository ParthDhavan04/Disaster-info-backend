import pandas as pd
import re

# Load your dataset (use your path!)
df = pd.read_csv("disaster_master_dataset.csv")

# Remove too-short rows (under 8 words)
df = df[df["clean_text"].str.split().str.len() > 8]

# Exclude "other" labeled texts that don't mention any disaster/impact keywords
def is_real_disaster(txt, label):
    if label != "other":
        return True
    txt = str(txt).lower()
    keywords = ["flood", "earthquake", "fire", "cyclone","landslide","killed","destroyed","injured","evacuated","deaths","casualties"]
    return any(k in txt for k in keywords)
df = df[df.apply(lambda x: is_real_disaster(x["clean_text"], x["disaster_label"]), axis=1)]

# Auto-fill severity labels by rule-based matching
def auto_severity(txt):
    txt_l = str(txt).lower()
    # Strong signals of high severity
    if re.search(r"\b(deaths?|killed|destroyed|collapsed|evacuated|casualties|major disaster|emergency)\b", txt_l):
        return "High"
    # Medium signals
    if re.search(r"\b(injured|damaged|rescued|blocked|moderate)\b", txt_l):
        return "Medium"
    return "Low"
df["severity_label"] = df["clean_text"].apply(auto_severity)

# Clean/fill engagement/media_urls fields
df["engagement"] = df["engagement"].fillna(0)
df["media_urls"] = df["media_urls"].apply(lambda x: x if str(x).startswith("http") else "")

# Optional: Geo enrichment (for now, just keep location_text if present)
# You can add spaCy/transformers/geopy logic here if desired.

# Safe default for validated
df["validated"] = df["validated"].fillna(False)

# Save for ML/labeling/production
df.to_csv("disaster_master_ml_ready.csv", index=False, encoding="utf-8")
print("ML Ready:", df.shape)
print("Disaster label counts:\n", df["disaster_label"].value_counts())
print("Severity label counts:\n", df["severity_label"].value_counts())
