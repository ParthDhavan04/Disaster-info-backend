import pandas as pd
import spacy
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time

INPUT_PATH = "disaster_master_ml_ready.csv"
OUTPUT_PATH = "disaster_master_geo_ner.csv"

# Load spaCy small English model
nlp = spacy.load("en_core_web_sm")
geolocator = Nominatim(user_agent="disaster-geo-script")

df = pd.read_csv(INPUT_PATH)
tqdm.pandas()

def extract_location(text):
    doc = nlp(str(text))
    locs = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]]
    # Return first best candidate, or join all as fallback
    return locs[0] if locs else ""

def geocode_location(location):
    if not location or str(location).strip() == "":
        return "", ""
    try:
        loc = geolocator.geocode(location, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
        else:
            return "", ""
    except Exception as e:
        # Sometimes overlimit, add sleep to avoid Nominatim rate limit
        time.sleep(1)
        return "", ""

print("Extracting locations (NER)...")
df["ner_location"] = df["clean_text"].progress_apply(extract_location)

print("Geocoding locations...")
lat_list = []
lon_list = []
for loc in tqdm(df["ner_location"]):
    lat, lon = geocode_location(loc)
    lat_list.append(lat)
    lon_list.append(lon)
    time.sleep(0.5)  # Be respectful to Nominatim API rate

df["lat"] = lat_list
df["lon"] = lon_list

# Optionally: prioritize ner_location for 'location_text' if empty
df["location_text"] = df.apply(lambda x: x["ner_location"] if not str(x.get("location_text", "")).strip() else x["location_text"], axis=1)

df.to_csv(OUTPUT_PATH, index=False)
print("Saved enriched data:", OUTPUT_PATH)
print(df[["clean_text","ner_location","lat","lon"]].sample(10))
