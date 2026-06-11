# WorldCup Fantasy Agent — Devpost Submission

## Tagline
> AI-powered 2026 FIFA World Cup Fantasy League agent — built on Google Cloud Vertex AI, 
> MongoDB Atlas MCP, and Gemini — that creates leagues, tracks 104+ real matches, 
> saves predictions, and takes action across multi-step tasks.

---

## What it does
WorldCup Fantasy Agent (WCA) is a fully functional AI agent for the 2026 FIFA World Cup. 
Users interact with a natural language chat interface that:

- **Browses real match data** — 104+ seeded 2026 World Cup matches (Group stage → Final)
- **Creates fantasy leagues** — the agent creates leagues in MongoDB in real time via tool calling
- **Saves predictions** — users predict match outcomes; agent stores and retrieves them
- **Handles multi-step tasks** — e.g. "Show Group A matches, create a league, and predict Argentina wins"
- **Shares socially** — generates Twitter/X share cards with one click
- **Goes beyond chat** — every agent response can trigger 1–5 real database operations

---

## How we built it

**AI Layer — Vertex AI (Gemini 2.0 Flash)**  
The core agent runs on Google Cloud Vertex AI using Gemini's native function calling. 
An agentic loop (up to 5 iterations) handles multi-step tool use within a single user message.

**Tool Layer — MongoDB Atlas MCP Server**  
We run a MongoDB MCP Toolbox server exposing 6 tools:
`get_matches`, `search_matches`, `get_leagues`, `create_league`, `save_prediction`, `get_stats`

The agent calls these tools in sequence to complete complex requests — this is the 
"goes beyond chat, takes action" requirement of the hackathon.

**Data Layer — MongoDB Atlas**  
Real 2026 World Cup match data (104+ matches) seeded from openfootball JSON into 
MongoDB Atlas. Collections: matches, leagues, predictions.

**Frontend — Streamlit**  
5-tab interface: Home, Matches, Leagues, Predictions & Social, AI Agent chat.
Dark World Cup theme with country flags, match cards, live stats.

**Infrastructure — Google Cloud**  
- Vertex AI (Gemini model hosting + function calling)
- Cloud Run (deployment)
- Google Cloud Agent Builder (agent orchestration)
- Service Account auth

---

## Challenges we ran into
- MongoDB Atlas SSL handshake failures required multi-strategy TLS fallback logic
- Vertex AI model availability varies by region — implemented region+model combo fallback
- GCP organisation policy forced service-account-bound credentials instead of standard API keys
- Balancing the agentic loop depth vs response latency

---

## Accomplishments we're proud of
- Fully functional multi-step agent that actually writes to a database
- 104+ real World Cup matches seeded and queryable
- Clean, polished World Cup themed UI
- Robust fallback logic for both MongoDB and Vertex AI connections
- MCP server properly integrated as agent tools

---

## What we learned
- Vertex AI function calling with multi-turn agentic loops
- MongoDB MCP Toolbox server setup and tool registration
- Google Cloud service account auth patterns
- Building production-grade agent error handling and fallbacks

---

## What's next
- Deploy permanent Cloud Run URL
- Add Google Search grounding for live match scores
- Leaderboard with scoring algorithm
- WhatsApp/Telegram bot interface
- Bracket prediction tournament mode

---

## Tech Stack
| Component | Technology |
|-----------|-----------|
| AI Model | Vertex AI — Gemini 2.0 Flash |
| Agent Orchestration | Google Cloud Agent Builder |
| Database | MongoDB Atlas |
| MCP Server | MongoDB MCP Toolbox |
| Frontend | Streamlit |
| Deployment | Google Cloud Run |
| Auth | GCP Service Account |
| Data | openfootball 2026 World Cup JSON |

---

## Links
- GitHub: https://github.com/MU3M4/worldcup-fantasy-agent
- Demo: [Cloud Run URL — add after deployment]
- Demo Video: [YouTube link — add after recording]
