import pymongo
import requests
import json

# === PASTE YOUR FULL CONNECTION STRING HERE ===
MONGODB_URI = "mongodb+srv://emmanuelmuemam_db_user:gcnzdWdqZ6eqeXoI@cluster0.jvcntai.mongodb.net/?appName=Cluster0"

client = pymongo.MongoClient(MONGODB_URI)
db = client["worldcup_fantasy"]

print("Seeding World Cup 2026 data...")

# Load fixtures from openfootball (reliable free source)
url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
try:
    data = requests.get(url, timeout=10).json()
    matches = data.get("matches", []) if isinstance(data, dict) else data
    
    # Clear old data and seed new
    db.matches.drop()
    if matches:
        db.matches.insert_many(matches)
        print(f"✅ Seeded {len(matches)} matches into 'matches' collection!")
    else:
        print("⚠️ No matches found in JSON.")
except Exception as e:
    print(f"Error loading fixtures: {e}")

# Create sample leagues collection (for demo)
db.leagues.insert_one({
    "name": "HackersUnited",
    "participants": 6,
    "status": "active",
    "created_at": "2026-06-10"
})

print("✅ Sample league created!")
print("\nCurrent collections:", db.list_collection_names())