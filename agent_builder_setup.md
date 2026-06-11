# Vertex AI Agent Builder Setup Guide
## Connect your MCP server as an official Agent Builder tool

---

## Step 1 — Open Agent Builder
Go to:
https://console.cloud.google.com/agent-builder?project=worldcup-fantasy-agent

Click **"Create App"** → Select **"Agent"**

---

## Step 2 — Configure the agent
- **Display name:** WorldCup Fantasy Agent  
- **Region:** us-central1  
- **Model:** gemini-2.0-flash (select latest available)  
- **System instruction:** (paste this)

```
You are WCA (WorldCup Fantasy Agent), an AI assistant for the 2026 FIFA World Cup 
Fantasy League platform. You have access to live MongoDB data with 104+ real matches.
Help users browse matches, create fantasy leagues, make predictions, and share on social media.
Handle multi-step requests in a single turn. Be enthusiastic and football-savvy.
```

---

## Step 3 — Enable Grounding (Google Search)
In the agent settings:
- Toggle ON **"Ground with Google Search"**
- This lets the agent answer "who won last night" with real data

---

## Step 4 — Add your MCP tools as OpenAPI tools
Click **"Tools"** → **"+ Create Tool"** → **"OpenAPI"**

Paste this OpenAPI spec (update the URL with your current ngrok):

```yaml
openapi: 3.0.0
info:
  title: WCA MongoDB MCP Tools
  version: 1.0.0
servers:
  - url: https://YOUR-NGROK-URL.ngrok-free.app
paths:
  /get_matches:
    post:
      operationId: get_matches
      summary: Fetch World Cup 2026 matches
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                limit:
                  type: integer
                group:
                  type: string
      responses:
        '200':
          description: List of matches
  /create_league:
    post:
      operationId: create_league
      summary: Create a new fantasy league
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [name]
              properties:
                name:
                  type: string
                participants:
                  type: integer
      responses:
        '200':
          description: Created league
  /save_prediction:
    post:
      operationId: save_prediction
      summary: Save a match prediction
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [match, prediction]
              properties:
                match:
                  type: string
                prediction:
                  type: string
                user:
                  type: string
      responses:
        '200':
          description: Saved prediction
```

---

## Step 5 — Get your Agent ID
After saving, copy the agent ID from the URL bar:
`https://console.cloud.google.com/agent-builder/locations/us-central1/agents/AGENT_ID_HERE`

Add it to `.streamlit/secrets.toml`:
```toml
AGENT_ID = "your-agent-id-here"
```

---

## Step 6 — Test in Agent Builder console
Use the built-in test chat on the right side:
- "Show me 5 World Cup matches"
- "Create a league called TestFC for 8 players"  
- "Who won the World Cup in 2022?" (uses Google Search grounding)

If all 3 work → your agent is fully configured ✅
