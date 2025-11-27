import spacy

try:
    nlp = spacy.load("en_core_web_sm")
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

text = "OMG, huge chunk of the hill just collapsed onto the highway near Solan, HP! Road totally blocked. NDRF teams needed ASAP"

doc = nlp(text)

print(f"Analyzing text: '{text}'")
print("-" * 30)
found = False
for ent in doc.ents:
    print(f"Entity: {ent.text}, Label: {ent.label_}")
    if ent.label_ in ['GPE', 'LOC']:
        found = True

if not found:
    print("No GPE or LOC entities found.")
