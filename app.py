import streamlit as st
import pymongo
from datetime import datetime
import json
import os
import asyncio
import requests
from zoneinfo import ZoneInfo



# ADK Imports
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import FunctionTool

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WCA – WorldCup Fantasy Agent",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CONFIG ───────────────────────────────────────────────────────────────────
MONGODB_URI  = "mongodb+srv://emmanuelmuemam_db_user:gcnzdWdqZ6eqeXoI@cluster0.jvcntai.mongodb.net/?retryWrites=true&w=majority"
GCP_PROJECT  = "project-d12993b2-a144-455d-ae0"
GCP_LOCATION = "us-central1"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #080e1f; }
[data-testid="stHeader"]           { background: #080e1f; }
[data-testid="stSidebar"]          { background: #0d1426; border-right: 1px solid #1e2a45; }
section.main > div                 { padding-top: 1.2rem; }
h1 { color: #f5a623 !important; font-size: 2rem !important; letter-spacing: -0.5px; }
h2, h3 { color: #e8eaf0 !important; }
p, li, label { color: #b0b8cc; }
.stTabs [data-baseweb="tab-list"]  { gap: 6px; background: transparent; }
.stTabs [data-baseweb="tab"]       { background: #131d35; color: #8899bb; border-radius: 8px;
                                     padding: 8px 18px; border: 1px solid #1e2a45; font-size: 14px; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #f5a623, #e8841a);
    color: #000 !important; font-weight: 700; border: none; }
.stButton > button {
    background: linear-gradient(135deg, #f5a623, #e8841a);
    color: #000 !important; font-weight: 600;
    border: none; border-radius: 8px; padding: 0.4rem 1.2rem; }
.stButton > button:hover { opacity: 0.88; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #131d35; color: #e8eaf0;
    border: 1px solid #1e2a45; border-radius: 8px; }
.match-card {
    background: #0d1426; border: 1px solid #1e2a45;
    border-radius: 12px; padding: 14px 20px;
    margin-bottom: 10px; display: flex;
    align-items: center; justify-content: space-between; }
.match-card:hover { border-color: #f5a623; transition: border-color 0.2s; }
.match-teams { font-size: 17px; font-weight: 600; color: #e8eaf0; }
.match-meta  { font-size: 12px; color: #6a7a9a; margin-top: 4px; }
.match-vs    { color: #f5a623; font-weight: 700; margin: 0 10px; }
.badge       { background: #1e2a45; color: #8899bb; font-size: 11px;
               padding: 3px 10px; border-radius: 20px; }
.badge.live  { background: #2a1a0d; color: #f5a623; border: 1px solid #f5a62344; }
.league-card { background: #0d1426; border: 1px solid #1e2a45;
               border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; }
.league-name { font-size: 16px; font-weight: 600; color: #f5a623; }
hr { border-color: #1e2a45; }
[data-testid="stMetric"] { background: #0d1426; border-radius: 10px;
                           padding: 12px 16px; border: 1px solid #1e2a45; }
[data-testid="stMetricValue"] { color: #f5a623 !important; }
</style>
""", unsafe_allow_html=True)

# ── MongoDB ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    if not MONGODB_URI or "YOUR_USER" in MONGODB_URI: return None
    common = dict(serverSelectionTimeoutMS=15000, connectTimeoutMS=10000, socketTimeoutMS=10000)
    for opts in [
        dict(**common, tls=True, tlsAllowInvalidCertificates=True),
        dict(**common, tls=False),
        dict(**common),
    ]:
        try:
            client = pymongo.MongoClient(MONGODB_URI, **opts)
            client.admin.command("ping")
            return client["worldcup_fantasy"]
        except Exception as e:
            last_err = e
    raise ConnectionError(f"MongoDB failed: {last_err}")

try:
    db = get_db()
    MONGO_OK = db is not None
    MONGO_ERROR = None
except Exception as _e:
    db = None
    MONGO_OK = False
    MONGO_ERROR = str(_e)

# ── Flags ─────────────────────────────────────────────────────────────────────
COUNTRY_FLAGS = {
    "Argentina": "🇦🇷", "Brazil": "🇧🇷", "France": "🇫🇷", "Germany": "🇩🇪",
    "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Portugal": "🇵🇹", "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪", "Uruguay": "🇺🇾", "Colombia": "🇨🇴", "Mexico": "🇲🇽",
    "USA": "🇺🇸", "Canada": "🇨🇦", "Morocco": "🇲🇦", "Senegal": "🇸🇳",
    "Japan": "🇯🇵", "South Korea": "🇰🇷", "Australia": "🇦🇺", "Saudi Arabia": "🇸🇦",
    "Croatia": "🇭🇷", "Switzerland": "🇨🇭", "Denmark": "🇩🇰", "Poland": "🇵🇱",
    "Ecuador": "🇪🇨", "Cameroon": "🇨🇲", "Ghana": "🇬🇭", "Tunisia": "🇹🇳",
    "Iran": "🇮🇷", "Serbia": "🇷🇸", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Costa Rica": "🇨🇷",
    "Qatar": "🇶🇦", "Italy": "🇮🇹", "TBD": "🏳️",
    "ARG": "🇦🇷", "BRA": "🇧🇷", "FRA": "🇫🇷", "GER": "🇩🇪", "ESP": "🇪🇸",
    "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "POR": "🇵🇹", "NED": "🇳🇱", "BEL": "🇧🇪", "URU": "🇺🇾",
    "COL": "🇨🇴", "MEX": "🇲🇽", "USA": "🇺🇸", "CAN": "🇨🇦", "MAR": "🇲🇦",
    "SEN": "🇸🇳", "JPN": "🇯🇵", "KOR": "🇰🇷", "AUS": "🇦🇺", "KSA": "🇸🇦",
    "CRO": "🇭🇷", "SUI": "🇨🇭", "DEN": "🇩🇰", "POL": "🇵🇱", "ECU": "🇪🇨",
    "CMR": "🇨🇲", "GHA": "🇬🇭", "TUN": "🇹🇳", "IRN": "🇮🇷", "SRB": "🇷🇸",
    "WAL": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "CRC": "🇨🇷", "QAT": "🇶🇦", "ITA": "🇮🇹",
}

def flag(team: str) -> str:
    if not team or team.upper() == "TBD": return "🏳️"
    t = team.strip()
    if t.upper() in COUNTRY_FLAGS: return COUNTRY_FLAGS[t.upper()]
    for name, emoji in COUNTRY_FLAGS.items():
        if name.lower() == t.lower(): return emoji
    for name, emoji in COUNTRY_FLAGS.items():
        if name.lower() in t.lower() or t.lower() in name.lower(): return emoji
    return "🏳️"

# ── Timezone Helper ───────────────────────────────────────────────────────────
def format_match_time(date_str):
    if not date_str: return "TBD"
    try:
        date_str = str(date_str)
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            user_tz_name = st.session_state.get("user_tz", "America/New_York")
            user_tz = ZoneInfo(user_tz_name)
            return dt.astimezone(user_tz).strftime("%b %d, %I:%M %p %Z")
        return date_str
    except Exception:
        return str(date_str)

# ── Agent Tool Functions (Direct MongoDB) ─────────────────────────────────────
def get_matches_tool(limit: int = 10, group: str = None) -> dict:
    """Get World Cup matches from database"""
    if not MONGO_OK: return {"error": "MongoDB not connected"}
    try:
        query = {}
        if group:
            # Try multiple possible formats
            group_upper = group.upper()
            query = {
                "$or": [
                    {"group": group_upper},
                    {"group": f"Group {group_upper}"},
                    {"group": {"$regex": f".*{group_upper}.*", "$options": "i"}}
                ]
            }
        matches = list(db.matches.find(query).limit(limit))
        for m in matches:
            m["_id"] = str(m["_id"])
        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}

def get_leagues_tool() -> dict:
    """Get all fantasy leagues"""
    if not MONGO_OK: return {"error": "MongoDB not connected"}
    try:
        leagues = list(db.leagues.find())
        for l in leagues:
            l["_id"] = str(l["_id"])
        return {"leagues": leagues, "count": len(leagues)}
    except Exception as e:
        return {"error": str(e)}

def save_prediction_tool(match: str, prediction: str, user: str = "player1") -> dict:
    """Save a match prediction"""
    if not MONGO_OK: return {"error": "MongoDB not connected"}
    try:
        result = db.predictions.insert_one({
            "match": match,
            "prediction": prediction,
            "user": user,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True, "prediction_id": str(result.inserted_id)}
    except Exception as e:
        return {"error": str(e)}

def create_league_tool(name: str, participants: int = 8) -> dict:
    """Create a new fantasy league"""
    if not MONGO_OK: return {"error": "MongoDB not connected"}
    try:
        result = db.leagues.insert_one({
            "name": name,
            "participants": participants,
            "scoring": "standard",
            "status": "active",
            "created": datetime.now().isoformat()
        })
        return {"success": True, "league_id": str(result.inserted_id), "name": name}
    except Exception as e:
        return {"error": str(e)}

def get_stats_tool() -> dict:
    """Get database statistics"""
    if not MONGO_OK: return {"error": "MongoDB not connected"}
    try:
        return {
            "total_matches": db.matches.count_documents({}),
            "total_leagues": db.leagues.count_documents({}),
            "total_predictions": db.predictions.count_documents({}),
            "active_leagues": db.leagues.count_documents({"status": "active"})
        }
    except Exception as e:
        return {"error": str(e)}

# UI Tab helper functions
def tool_get_stats():
    return get_stats_tool()

def tool_create_league(name, participants, scoring):
    return create_league_tool(name, participants)

def tool_save_prediction(match, prediction, user):
    return save_prediction_tool(match, prediction, user)

SYSTEM_PROMPT = """You are WCA (WorldCup Fantasy Agent), an expert AI assistant for the 2026 FIFA World Cup Fantasy League platform built on Google Cloud.
You are powered by Gemini via the Agent Development Kit (ADK) and connected to a live MongoDB database.
Your capabilities: Browse matches, create leagues, save predictions, get stats.
Personality: Enthusiastic, knowledgeable football expert. Use emoji. Be concise.
Actions: When asked to DO something, use your tools and confirm the action."""

# ── GOOGLE ADK AGENT SETUP ────────────────────────────────────────────────────
@st.cache_resource
def get_adk_runner():
    try:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT
        os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_LOCATION
        
        # Convert to ADK FunctionTools
        agent_tools = [
            FunctionTool(get_matches_tool),
            FunctionTool(get_leagues_tool),
            FunctionTool(save_prediction_tool),
            FunctionTool(create_league_tool),
            FunctionTool(get_stats_tool),
        ]
        
        agent = LlmAgent(
            model='gemini-2.5-flash',
            name='wca_agent',
            instruction=SYSTEM_PROMPT,
            tools=agent_tools
        )
        
        session_service = InMemorySessionService()
        runner = Runner(app_name='wca_app', agent=agent, session_service=session_service)
        return runner, session_service, True, "Vertex AI Agent Builder + MongoDB"
    except Exception as e:
        return None, None, False, str(e)

async def run_adk_async(runner, prompt: str, session_id: str):
    content = types.Content(role='user', parts=[types.Part(text=prompt)])
    events = runner.run_async(session_id=session_id, user_id='user1', new_message=content)
    response_text = ""
    async for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    return response_text

def call_adk_agent(prompt: str):
    runner, session_service, ok, info = get_adk_runner()
    if not ok: return f"⚠️ Agent Error: {info}"
    
    if "adk_session_id" not in st.session_state:
        async def create_sess():
            sess = await session_service.create_session(state={}, app_name='wca_app', user_id='user1')
            return sess.id
        st.session_state["adk_session_id"] = asyncio.run(create_sess())
    
    try:
        return asyncio.run(run_adk_async(runner, prompt, st.session_state["adk_session_id"]))
    except Exception as e:
        return f"⚠️ Agent execution error: {str(e)}"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚽ WCA Control Panel")
    
    user_tz = st.selectbox(
        "🌍 Your Timezone", 
        ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo", "UTC"],
        index=0
    )
    st.session_state["user_tz"] = user_tz
    st.divider()
    
    if not MONGO_OK:
        st.error("❌ MongoDB disconnected")
        if MONGO_ERROR: st.caption(MONGO_ERROR[:100])
    else:
        try:
            stats = tool_get_stats()
            col_a, col_b = st.columns(2)
            col_a.metric("Matches", stats.get("total_matches", 0))
            col_b.metric("Leagues", stats.get("active_leagues", 0))
            col_c, col_d = st.columns(2)
            col_c.metric("Predictions", stats.get("total_predictions", 0))
            col_d.metric("Players", "∞")
        except: pass

    st.divider()
    _, _, adk_ok, adk_info = get_adk_runner()
    if adk_ok:
        st.success(f"✅ AI: {adk_info}")
    else:
        st.error(f"❌ AI: {adk_info[:60]}")
    
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_resource.clear()
        st.rerun()
    st.caption(f"GCP: `{GCP_PROJECT}`")
    st.caption("Google Cloud Rapid Agent Hackathon 2026")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🌍 WorldCup Fantasy Agent ⚽")
st.markdown("<p style='color:#6a7a9a;margin-top:-10px'>2026 FIFA World Cup · Vertex AI (Gemini) · MongoDB Atlas · Google Cloud Agent Builder (ADK)</p>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "📅 Matches", "🏆 Leagues", "🔮 Predictions", "🤖 AI Agent"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — HOME
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.markdown("""<div class="league-card"><div style="font-size:2rem">🏆</div><div class="league-name">Fantasy Leagues</div><p>Create leagues, invite friends, compete on predictions</p></div>""", unsafe_allow_html=True)
    c2.markdown("""<div class="league-card"><div style="font-size:2rem">📊</div><div class="league-name">104+ Real Matches</div><p>Seeded from openfootball · Group stage through Final</p></div>""", unsafe_allow_html=True)
    c3.markdown("""<div class="league-card"><div style="font-size:2rem">🤖</div><div class="league-name">Gemini AI Agent</div><p>Multi-step tasks · Live tool calling · Google Cloud</p></div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🔥 Featured Matches")
    if MONGO_OK:
        try:
            for m in list(db.matches.find().limit(4)):
                t1, t2 = m.get("team1","TBD"), m.get("team2","TBD")
                st.markdown(f"""<div class="match-card"><div><div class="match-teams">{flag(t1)} {t1} <span class="match-vs">vs</span> {t2} {flag(t2)}</div><div class="match-meta">📅 {format_match_time(m.get('date',''))} &nbsp;·&nbsp; <span class="badge">{m.get('group','')}</span></div></div><div style="color:#f5a623;font-size:20px">⚡</div></div>""", unsafe_allow_html=True)
        except Exception as e: st.error(f"Could not load matches: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MATCHES
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📅 World Cup 2026 Matches")
    cf1, cf2, cf3 = st.columns([2, 1, 1])
    with cf1: search_team = st.text_input("🔍 Search team", placeholder="e.g. Argentina")
    with cf2: limit_n = st.selectbox("Show", [10, 20, 50, 104], index=0)
    with cf3: group_filter = st.selectbox("Group", ["All", "A","B","C","D","E","F","G","H"], index=0)
    if MONGO_OK:
        try:
            query = {}
            if search_team: query = {"$or": [{"team1": {"$regex": search_team, "$options": "i"}}, {"team2": {"$regex": search_team, "$options": "i"}}]}
            if group_filter != "All": query["group"] = group_filter
            matches = list(db.matches.find(query).limit(limit_n))
            st.caption(f"Showing {len(matches)} matches")
            for m in matches:
                t1, t2 = m.get("team1","TBD"), m.get("team2","TBD")
                st.markdown(f"""<div class="match-card"><div><div class="match-teams">{flag(t1)} {t1} <span class="match-vs">vs</span> {t2} {flag(t2)}</div><div class="match-meta">📅 {format_match_time(m.get('date',''))} &nbsp;·&nbsp; 🏟️ {m.get('venue','')} &nbsp; <span class='badge'>{m.get('group','')}</span></div></div></div>""", unsafe_allow_html=True)
        except Exception as e: st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LEAGUES
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🏆 Fantasy Leagues")
    if MONGO_OK:
        try:
            leagues = list(db.leagues.find())
            if leagues:
                for lg in leagues:
                    st.markdown(f"""<div class="league-card"><div style="display:flex;justify-content:space-between;align-items:center"><div><div class="league-name">🏆 {lg.get('name','Unnamed')}</div><div style="color:#6a7a9a;font-size:13px;margin-top:4px">👥 {lg.get('participants','?')} players · 📊 {lg.get('scoring','standard')}</div></div><span class="badge {'live' if lg.get('status')=='active' else ''}">{lg.get('status','active').upper()}</span></div></div>""", unsafe_allow_html=True)
            else: st.info("No leagues yet — create one below or ask the AI Agent!")
        except Exception as e: st.error(f"Error: {e}")
    st.divider()
    st.markdown("### ➕ Create New League")
    lc1, lc2, lc3 = st.columns(3)
    with lc1: league_name = st.text_input("League Name", "WorldCupElite2026")
    with lc2: participants = st.number_input("Players", 2, 32, 8)
    with lc3: scoring_mode = st.selectbox("Scoring", ["standard", "advanced"])
    if st.button("🚀 Create League"):
        result = tool_create_league(league_name, participants, scoring_mode)
        if result.get("success"): st.success(f"✅ League **{league_name}** created!"); st.rerun()
        else: st.error(result.get("error", "Failed"))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🔮 Predictions & Social Sharing")
    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown("#### 📝 Make a Prediction")
        try:
            match_list = list(db.matches.find().limit(50)) if MONGO_OK else []
            match_options = [f"{m.get('team1','TBD')} vs {m.get('team2','TBD')}" for m in match_list] or ["Argentina vs Brazil"]
        except: match_options = ["Argentina vs Brazil"]
        match_choice = st.selectbox("Select Match", match_options)
        pred_winner = st.text_input("Predicted Winner", "Argentina")
        pred_score = st.text_input("Predicted Score", "2-1")
        username = st.text_input("Your Name", "Player1")
        if st.button("💾 Save Prediction"):
            result = tool_save_prediction(match_choice, f"{pred_winner} wins {pred_score}", username)
            if result.get("success"): st.success(f"✅ Saved!"); st.session_state["last_prediction"] = {"match": match_choice, "winner": pred_winner, "score": pred_score, "user": username}
    with pc2:
        st.markdown("#### 📢 Social Sharing")
        last = st.session_state.get("last_prediction", {"match": "Argentina vs Brazil", "winner": "Argentina", "score": "2-1", "user": "Player1"})
        share_text = f"🔥 My #WorldCup2026 Prediction!\n⚽ {last['match']}\n🏆 Winner: {last['winner']}\n📊 Score: {last['score']}\nBuilt with @GoogleCloud Vertex AI + MongoDB"
        st.text_area("Share Card", share_text, height=180)
    st.divider()
    st.markdown("#### 🕐 Recent Predictions")
    if MONGO_OK:
        try:
            preds = list(db.predictions.find().sort("timestamp", -1).limit(5))
            for p in preds: st.markdown(f"""<div class="match-card"><div><div class="match-teams" style="font-size:14px">⚽ {p.get('match','?')}</div><div class="match-meta">🔮 {p.get('prediction','?')} · 👤 {p.get('user','?')}</div></div></div>""", unsafe_allow_html=True)
        except: pass

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — AI AGENT
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🤖 WCA AI Agent")
    _, _, adk_ok, adk_info = get_adk_runner()
    if adk_ok:
        st.success(f"✅ Powered by **Google ADK (Agent Builder)** · Tools Active · MongoDB {'✅' if MONGO_OK else '❌'}")
    else:
        st.error(f"❌ Agent offline: {adk_info[:80]}")
    st.caption("Multi-step AI agent: ask it to show matches, create leagues, save predictions — all in one message.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": "👋 Hi! I'm **WCA**, powered by **Google Cloud Agent Builder (ADK)** and connected to your MongoDB. What would you like to do? ⚽"}]

    st.markdown("**⚡ Try these multi-step prompts:**")
    qc = st.columns(4)
    multi_prompts = ["Show Group A matches then give me stats", "Create league 'HackathonFC' for 12 players", "Find Argentina matches and predict 2-0 win", "Show all leagues"]
    for i, (col, prompt) in enumerate(zip(qc, multi_prompts)):
        if col.button(prompt, key=f"qp_{i}"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("🤖 Agent thinking & calling tools..."):
                reply = call_adk_agent(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    st.divider()
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="⚽" if msg["role"] == "assistant" else None):
            st.write(msg["content"])

    user_input = st.chat_input("Ask anything — multi-step requests welcome…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("🤖 Agent thinking & calling tools..."):
            reply = call_adk_agent(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = [{"role": "assistant", "content": "Chat cleared! How can I help? ⚽"}]
        if "adk_session_id" in st.session_state: del st.session_state["adk_session_id"]
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("<p style='text-align:center;color:#3a4a6a;font-size:12px'>WorldCup Fantasy Agent · Google Cloud Rapid Agent Hackathon 2026 · Vertex AI (Gemini) · MongoDB Atlas · Streamlit</p>", unsafe_allow_html=True)