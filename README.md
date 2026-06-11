# 🌍 WorldCup Fantasy Agent (WCA)

**Google Cloud Rapid Agent Hackathon 2026 Submission**

An autonomous AI Agent for 2026 FIFA World Cup Fantasy Leagues with real data persistence via **MongoDB MCP**.

### Features
- 104+ real World Cup 2026 matches seeded
- Create & manage fantasy leagues
- Make & save predictions
- Social sharing (X/Twitter ready)
- Vibrant, responsive Streamlit UI
- Full Gemini/Vertex AI agent with function calling (multi-step reasoning)

### Tech Stack
- **Frontend**: Streamlit (vibrant dark theme)
- **Database**: MongoDB Atlas + **MongoDB MCP Toolbox** (core "superpower")
- **AI**: Gemini via Vertex AI (service account auth)
- **Deployment**: Cloud Run (public URL)

### Setup
```bash
pip install -r requirements.txt
streamlit run app.py