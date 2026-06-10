# WorldCup Fantasy Agent — Setup Instructions

## Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

## Step 2 — Download your service account key
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=worldcup-fantasy-agent
2. Click `worldcup-fantasy-agent@appspot.gserviceaccount.com`
3. **Keys** tab → **Add Key** → **Create new key** → **JSON** → Download
4. Rename the downloaded file to `service_account.json`
5. Place it in your project root (same folder as `app.py`)

## Step 3 — Grant Vertex AI permissions to the service account
1. Go to: https://console.cloud.google.com/iam-admin/iam?project=worldcup-fantasy-agent
2. Find `worldcup-fantasy-agent@appspot.gserviceaccount.com`
3. Click the pencil (edit) icon
4. Add role: **Vertex AI User**
5. Save

## Step 4 — Enable Vertex AI API (if not already)
Visit: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=worldcup-fantasy-agent
Click **Enable**

## Step 5 — Create secrets file
```bash
mkdir -p .streamlit
cp secrets.toml.example .streamlit/secrets.toml
```

## Step 6 — Run the app
```bash
streamlit run app.py
```

App opens at: http://localhost:8501

## .gitignore — add these lines
```
service_account.json
.streamlit/secrets.toml
__pycache__/
*.pyc
```
