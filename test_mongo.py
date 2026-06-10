# save as test_mongo.py and run: python test_mongo.py
import pymongo

URI = "mongodb+srv://emmanuelmuemam_db_user:gcnzdWdqZ6eqeXoI@cluster0.jvcntai.mongodb.net/?appName=Cluster0"

# Try 1
try:
    c = pymongo.MongoClient(URI, tls=True, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=8000)
    c.admin.command("ping")
    print("✅ Strategy 1 works (tls=True, allowInvalidCerts)")
except Exception as e:
    print(f"❌ Strategy 1 failed: {e}")

# Try 2
try:
    c = pymongo.MongoClient(URI, tls=False, serverSelectionTimeoutMS=8000)
    c.admin.command("ping")
    print("✅ Strategy 2 works (tls=False)")
except Exception as e:
    print(f"❌ Strategy 2 failed: {e}")

# Try 3 — with certifi
try:
    import certifi
    c = pymongo.MongoClient(URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=8000)
    c.admin.command("ping")
    print("✅ Strategy 3 works (certifi)")
except Exception as e:
    print(f"❌ Strategy 3 failed: {e}")