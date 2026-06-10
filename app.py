import streamlit as st
import pymongo
from datetime import datetime
import json
import os

# ── Page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="WCA – WorldCup Fantasy Agent",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CONFIG ───────────────────────────────────────────────────────────────────
MONGODB_URI      = "mongodb+srv://emmanuelmuemam_db_user:gcnzdWdqZ6eqeXoI@cluster0.jvcntai.mongodb.net/?appName=Cluster0"
MCP_URL          = "https://3a3a-102-212-236-204.ngrok-free.app"
GCP_PROJECT      = st.secrets.get("GCP_PROJECT", "worldcup-fantasy-agent")
GCP_LOCATION     = st.secrets.get("GCP_LOCATION", "us-central1")
SA_KEY_PATH      = st.secrets.get("SA_KEY_PATH", "service_account.json")   # path to downloaded JSON

# ── Custom CSS theme ─────────────────────────────────────────────────────────
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
.match-card:hover { border-color: #f5a623; }
.match-teams { font-size: 17px; font-weight: 600; color: #e8eaf0; }
.match-meta  { font-size: 12px; color: #6a7a9a; margin-top: 4px; }
.match-vs    { color: #f5a623; font-weight: 700; margin: 0 10px; }
.badge       { background: #1e2a45; color: #8899bb; font-size: 11px;
               padding: 3px 10px; border-radius: 20px; }
.badge.live  { background: #2a1a0d; color: #f5a623; border: 1px solid #f5a62344; }
.league-card {
    background: #0d1426; border: 1px solid #1e2a45;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; }
.league-name { font-size: 16px; font-weight: 600; color: #f5a623; }
hr { border-color: #1e2a45; }
[data-testid="stDataFrame"] { background: #0d1426; border-radius: 10px; }
[data-testid="stMetric"] { background: #0d1426; border-radius: 10px; padding: 12px 16px;
                           border: 1px solid #1e2a45; }
[data-testid="stMetricValue"] { color: #f5a623 !important; }
</style>
""", unsafe_allow_html=True)


# ── MongoDB ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    """Try multiple SSL strategies to handle different environments."""
    common = dict(
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
    )
    strategies = [
        dict(**common, tls=True, tlsAllowInvalidCertificates=True),
        dict(**common, tls=False),
        dict(**common),
    ]
    last_err = None
    for opts in strategies:
        try:
            client = pymongo.MongoClient(MONGODB_URI, **opts)
            client.admin.command("ping")
            return client["worldcup_fantasy"]
        except Exception as e:
            last_err = e
            continue
    raise ConnectionError(f"MongoDB failed: {last_err}")

try:
    db = get_db()
    MONGO_OK = True
    MONGO_ERROR = None
except Exception as _mongo_exc:
    db = None
    MONGO_OK = False
    MONGO_ERROR = str(_mongo_exc)


# ── Country flag helper ───────────────────────────────────────────────────────
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
}

def flag(team: str) -> str:
    if not team or team == "TBD":
        return "🏳️"
    team_lower = team.lower().strip()
    # Exact match first
    for name, emoji in COUNTRY_FLAGS.items():
        if name.lower() == team_lower:
            return emoji
    # Partial match
    for name, emoji in COUNTRY_FLAGS.items():
        if name.lower() in team_lower or team_lower in name.lower():
            return emoji
    return "🏳️"


# ── MongoDB tool functions ────────────────────────────────────────────────────
def tool_get_matches(limit: int = 10, group: str = None) -> dict:
    query = {}
    if group:
        query["group"] = group.upper()
    matches = list(db.matches.find(query).limit(limit))
    for m in matches:
        m["_id"] = str(m["_id"])
    return {"matches": matches, "count": len(matches)}

def tool_get_leagues() -> dict:
    leagues = list(db.leagues.find())
    for l in leagues:
        l["_id"] = str(l["_id"])
    return {"leagues": leagues, "count": len(leagues)}

def tool_create_league(name: str, participants: int = 8, scoring: str = "standard") -> dict:
    result = db.leagues.insert_one({
        "name": name,
        "participants": participants,
        "scoring": scoring,
        "status": "active",
        "created": datetime.now().isoformat(),
    })
    return {"success": True, "league_id": str(result.inserted_id), "name": name}

def tool_save_prediction(match: str, prediction: str, user: str = "player1") -> dict:
    result = db.predictions.insert_one({
        "match": match,
        "prediction": prediction,
        "user": user,
        "timestamp": datetime.now().isoformat(),
    })
    return {"success": True, "prediction_id": str(result.inserted_id)}

def tool_get_stats() -> dict:
    return {
        "total_matches":    db.matches.count_documents({}),
        "total_leagues":    db.leagues.count_documents({}),
        "total_predictions":db.predictions.count_documents({}),
        "active_leagues":   db.leagues.count_documents({"status": "active"}),
    }

TOOLS_MAP = {
    "get_matches":     tool_get_matches,
    "get_leagues":     tool_get_leagues,
    "create_league":   tool_create_league,
    "save_prediction": tool_save_prediction,
    "get_stats":       tool_get_stats,
}

# ── Vertex AI initialisation (runs once) ─────────────────────────────────────
@st.cache_resource
def init_vertex():
    """Initialise Vertex AI using the service account JSON file."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part

        # Point ADC to the service account key
        if os.path.exists(SA_KEY_PATH):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY_PATH

        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

        # Build tool declarations
        declarations = [
            FunctionDeclaration(
                name="get_matches",
                description="Fetch upcoming or recent World Cup 2026 matches from the database.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max number of matches (default 10)"},
                        "group": {"type": "string",  "description": "Group letter A-H (optional)"},
                    },
                },
            ),
            FunctionDeclaration(
                name="get_leagues",
                description="List all fantasy leagues in the database.",
                parameters={"type": "object", "properties": {}},
            ),
            FunctionDeclaration(
                name="create_league",
                description="Create a new fantasy league.",
                parameters={
                    "type": "object",
                    "properties": {
                        "name":         {"type": "string",  "description": "League name"},
                        "participants": {"type": "integer", "description": "Number of players (default 8)"},
                        "scoring":      {"type": "string",  "description": "'standard' or 'advanced'"},
                    },
                    "required": ["name"],
                },
            ),
            FunctionDeclaration(
                name="save_prediction",
                description="Save a match prediction for the user.",
                parameters={
                    "type": "object",
                    "properties": {
                        "match":      {"type": "string", "description": "Match e.g. 'Argentina vs Brazil'"},
                        "prediction": {"type": "string", "description": "Predicted outcome or score"},
                        "user":       {"type": "string", "description": "Username (default 'player1')"},
                    },
                    "required": ["match", "prediction"],
                },
            ),
            FunctionDeclaration(
                name="get_stats",
                description="Get overall database statistics.",
                parameters={"type": "object", "properties": {}},
            ),
        ]

        system_instruction = (
            "You are WCA (WorldCup Fantasy Agent), an AI assistant for the 2026 FIFA World Cup "
            "Fantasy League platform. You help users browse real match data (104+ matches), "
            "create and manage fantasy leagues, make and track predictions, and get World Cup "
            "insights. Use the provided tools to fetch live data. Be enthusiastic, concise, and "
            "football-savvy. Respond in 2-4 sentences unless showing data."
        )
        wca_tools = [Tool(function_declarations=declarations)]

        # Try multiple regions + model names until one works
        combos = [
            ("us-central1",         "gemini-2.0-flash"),
            ("us-east1",            "gemini-2.0-flash"),
            ("europe-west1",        "gemini-2.0-flash"),
            ("us-central1",         "gemini-2.0-flash-lite"),
            ("us-east1",            "gemini-2.0-flash-lite"),
            ("us-central1",         "gemini-1.5-flash"),
            ("us-east1",            "gemini-1.5-flash"),
            ("europe-west1",        "gemini-1.5-flash"),
            ("us-central1",         "gemini-1.5-flash-002"),
            ("us-east1",            "gemini-1.5-flash-002"),
            ("us-central1",         "gemini-1.5-pro-002"),
            ("us-east1",            "gemini-1.5-pro-002"),
            ("global",              "gemini-2.0-flash"),
        ]
        last_model_err = None
        for region, mn in combos:
            try:
                vertexai.init(project=GCP_PROJECT, location=region)
                m = GenerativeModel(
                    model_name=mn,
                    system_instruction=system_instruction,
                    tools=wca_tools,
                )
                test = m.generate_content("ping")
                return m, True, f"✅ {mn} @ {region}"
            except Exception as me:
                last_model_err = f"{mn}@{region}: {str(me)[:80]}"
                continue
        raise Exception(f"No working model found. Last: {last_model_err}")

    except ImportError:
        return None, False, "install"
    except Exception as e:
        return None, False, str(e)


def call_vertex_agent(user_message: str, history: list) -> str:
    """Call Gemini via Vertex AI with function calling. Returns agent response string."""
    model, ok, err = init_vertex()

    if not ok:
        if err == "install":
            return "⚠️ `google-cloud-aiplatform` not installed.\n\nRun:\n```\npip install google-cloud-aiplatform\n```"
        if not os.path.exists(SA_KEY_PATH):
            return (
                f"⚠️ Service account key not found at `{SA_KEY_PATH}`.\n\n"
                "**Steps to fix:**\n"
                "1. Go to GCP Console → IAM & Admin → Service Accounts\n"
                "2. Click `worldcup-fantasy-agent@appspot.gserviceaccount.com`\n"
                "3. Keys tab → Add Key → Create new key → JSON → Download\n"
                "4. Save as `service_account.json` in your project folder\n"
                "5. Restart the app"
            )
        return f"⚠️ Vertex AI init error: {err}"

    try:
        from vertexai.generative_models import GenerativeModel, Part, Content

        # Convert history to Vertex AI Content format
        vertex_history = []
        for msg in history[-8:]:
            role = "user" if msg["role"] == "user" else "model"
            vertex_history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))

        chat = model.start_chat(history=vertex_history)
        response = chat.send_message(user_message)

        # Agentic loop — handle function calls
        max_loops = 4
        loop = 0
        while loop < max_loops:
            loop += 1

            # Collect all function call parts
            fn_calls = []
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call and part.function_call.name:
                        fn_calls.append(part.function_call)

            if not fn_calls:
                break

            # Execute each function and collect responses
            fn_response_parts = []
            for fc in fn_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}

                if fn_name in TOOLS_MAP:
                    try:
                        result = TOOLS_MAP[fn_name](**fn_args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Unknown tool: {fn_name}"}

                fn_response_parts.append(
                    Part.from_function_response(
                        name=fn_name,
                        response={"result": json.dumps(result, default=str)},
                    )
                )

            response = chat.send_message(fn_response_parts)

        # Extract text from final response
        text_parts = []
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

        return "\n".join(text_parts) if text_parts else "I couldn't generate a response. Please try again."

    except Exception as e:
        return f"⚠️ Agent error: {str(e)}\n\nMake sure your service account has the **Vertex AI User** role in IAM."


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚽ WCA Control Panel")
    st.divider()

    if not MONGO_OK:
        st.error("❌ MongoDB disconnected")
        if MONGO_ERROR:
            st.caption(MONGO_ERROR[:120])
    else:
        try:
            stats = tool_get_stats()
            col_a, col_b = st.columns(2)
            col_a.metric("Matches",     stats["total_matches"])
            col_b.metric("Leagues",     stats["active_leagues"])
            col_c, col_d = st.columns(2)
            col_c.metric("Predictions", stats["total_predictions"])
            col_d.metric("Players",     "∞")
        except Exception as e:
            st.warning(f"DB stats error: {e}")

    st.divider()
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

    st.caption(f"MCP: `{MCP_URL[:30]}…`")
    st.caption("Google Cloud Rapid Agent Hackathon 2026")

    # Vertex AI status
    st.divider()
    sa_exists = os.path.exists(SA_KEY_PATH)
    if sa_exists:
        st.success("✅ Service account key found")
        st.caption(f"Key: `{SA_KEY_PATH}`")
    else:
        st.warning("⚠️ `service_account.json` not found")
        st.caption("Download from GCP → IAM → Service Accounts → Keys")


# ── Main header ──────────────────────────────────────────────────────────────
st.markdown("# 🌍 WorldCup Fantasy Agent ⚽")
st.markdown(
    "<p style='color:#6a7a9a;margin-top:-10px'>"
    "2026 FIFA World Cup · AI-Powered Fantasy League Assistant · "
    "Vertex AI (Gemini 2.0 Flash) · MongoDB Atlas"
    "</p>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Home", "📅 Matches", "🏆 Leagues", "🔮 Predictions", "🤖 AI Agent"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — HOME
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.markdown("""
    <div class="league-card">
        <div style="font-size:2rem">🏆</div>
        <div class="league-name">Fantasy Leagues</div>
        <p>Create leagues, invite friends, compete on predictions</p>
    </div>""", unsafe_allow_html=True)
    col2.markdown("""
    <div class="league-card">
        <div style="font-size:2rem">📊</div>
        <div class="league-name">Real Match Data</div>
        <p>104+ seeded matches from openfootball · Group stage to Final</p>
    </div>""", unsafe_allow_html=True)
    col3.markdown("""
    <div class="league-card">
        <div style="font-size:2rem">🤖</div>
        <div class="league-name">Vertex AI Agent</div>
        <p>Gemini 2.0 Flash via Google Cloud · Live MongoDB tool calling</p>
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔥 Featured Matches")
    try:
        featured = list(db.matches.find().limit(3))
        for m in featured:
            t1       = m.get("team1", "TBD")
            t2       = m.get("team2", "TBD")
            date_str = m.get("date", "")
            st.markdown(f"""
            <div class="match-card">
                <div>
                    <div class="match-teams">
                        {flag(t1)} {t1}
                        <span class="match-vs">vs</span>
                        {t2} {flag(t2)}
                    </div>
                    <div class="match-meta">📅 {date_str} &nbsp;·&nbsp; <span class="badge">Group Stage</span></div>
                </div>
                <div style="color:#f5a623;font-size:20px">⚡</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load matches: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MATCHES
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📅 World Cup 2026 Matches")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_team = st.text_input("🔍 Filter by team", placeholder="e.g. Argentina")
    with col_f2:
        limit_n = st.selectbox("Show", [10, 20, 50, 104], index=0)

    try:
        query = {}
        if search_team:
            regex = {"$regex": search_team, "$options": "i"}
            query = {"$or": [{"team1": regex}, {"team2": regex}]}

        matches = list(db.matches.find(query).limit(limit_n))
        st.caption(f"Showing {len(matches)} matches")

        for m in matches:
            t1     = m.get("team1", "TBD")
            t2     = m.get("team2", "TBD")
            date   = m.get("date", "")
            grp    = m.get("group", "")
            venue  = m.get("venue", "")
            badge_html = f'<span class="badge">{grp}</span>' if grp else ""
            venue_html = f"&nbsp;·&nbsp; 🏟️ {venue}" if venue else ""
            st.markdown(f"""
            <div class="match-card">
                <div>
                    <div class="match-teams">
                        {flag(t1)} {t1}
                        <span class="match-vs">vs</span>
                        {t2} {flag(t2)}
                    </div>
                    <div class="match-meta">📅 {date}{venue_html}&nbsp; {badge_html}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Match load error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LEAGUES
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🏆 Fantasy Leagues")

    try:
        leagues = list(db.leagues.find())
        if leagues:
            for lg in leagues:
                name    = lg.get("name", "Unnamed")
                pax     = lg.get("participants", "?")
                status  = lg.get("status", "active")
                scoring = lg.get("scoring", "standard")
                created = lg.get("created", "")
                st.markdown(f"""
                <div class="league-card">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div class="league-name">🏆 {name}</div>
                            <div style="color:#6a7a9a;font-size:13px;margin-top:4px">
                                👥 {pax} players &nbsp;·&nbsp; 📊 {scoring} scoring
                                &nbsp;·&nbsp; {created[:10] if created else ""}
                            </div>
                        </div>
                        <span class="badge {'live' if status=='active' else ''}">{status.upper()}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No leagues yet — create your first one below!")
    except Exception as e:
        st.error(f"League load error: {e}")

    st.divider()
    st.markdown("### ➕ Create New League")
    col1, col2, col3 = st.columns(3)
    with col1:
        league_name = st.text_input("League Name", "WorldCupElite2026")
    with col2:
        participants = st.number_input("Players", 2, 32, 8)
    with col3:
        scoring_mode = st.selectbox("Scoring", ["standard", "advanced"])

    if st.button("🚀 Create League"):
        result = tool_create_league(league_name, participants, scoring_mode)
        if result["success"]:
            st.success(f"✅ League **{league_name}** created! ID: `{result['league_id']}`")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🔮 Predictions & Social Sharing")
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.markdown("#### 📝 Make a Prediction")
        try:
            match_list = list(db.matches.find().limit(30))
            match_options = [
                f"{m.get('team1','TBD')} vs {m.get('team2','TBD')}"
                for m in match_list
            ]
        except Exception:
            match_options = ["Argentina vs Brazil", "France vs Germany", "Spain vs England"]

        match_choice = st.selectbox("Select Match", match_options)
        pred_winner  = st.text_input("Predicted Winner", "Argentina")
        pred_score   = st.text_input("Predicted Score", "2-1")
        username     = st.text_input("Your Name", "Player1")

        if st.button("💾 Save Prediction"):
            full_pred = f"{pred_winner} wins {pred_score}"
            result = tool_save_prediction(match_choice, full_pred, username)
            if result["success"]:
                st.success(f"✅ Prediction saved! ID: `{result['prediction_id']}`")
                st.session_state["last_prediction"] = {
                    "match": match_choice, "winner": pred_winner,
                    "score": pred_score,   "user": username,
                }

    with col_p2:
        st.markdown("#### 📢 Social Sharing")
        last = st.session_state.get("last_prediction", {
            "match": "Argentina vs Brazil", "winner": "Argentina",
            "score": "2-1", "user": "Player1",
        })
        share_text = (
            f"🔥 My #WorldCup2026 Prediction!\n\n"
            f"⚽ {last['match']}\n"
            f"🏆 Winner: {last['winner']}\n"
            f"📊 Score: {last['score']}\n\n"
            f"Join my Fantasy League on WCA!\n"
            f"#FIFA2026 #FantasyFootball #WorldCupFantasy"
        )
        st.text_area("Share Card Text", share_text, height=180)
        tw_url = (
            "https://twitter.com/intent/tweet?text="
            + share_text.replace(" ", "%20").replace("#", "%23").replace("\n", "%0A")[:280]
        )
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(
                f'<a href="{tw_url}" target="_blank">'
                '<button style="background:linear-gradient(135deg,#1DA1F2,#0d8fd8);'
                'color:#fff;border:none;border-radius:8px;padding:8px 18px;'
                'font-weight:600;cursor:pointer;width:100%">🐦 Share on X</button></a>',
                unsafe_allow_html=True,
            )
        with col_s2:
            if st.button("📋 Copy Text"):
                st.code(share_text, language=None)

    st.divider()
    st.markdown("#### 🕐 Recent Predictions")
    try:
        preds = list(db.predictions.find().sort("timestamp", -1).limit(10))
        if preds:
            for p in preds:
                ts = p.get("timestamp", "")[:10] if p.get("timestamp") else ""
                st.markdown(f"""
                <div class="match-card">
                    <div>
                        <div class="match-teams" style="font-size:14px">⚽ {p.get('match','?')}</div>
                        <div class="match-meta">
                            🔮 {p.get('prediction','?')} &nbsp;·&nbsp;
                            👤 {p.get('user','?')} &nbsp;·&nbsp; 📅 {ts}
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No predictions yet.")
    except Exception as e:
        st.error(f"Predictions error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — AI AGENT CHAT (Vertex AI)
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🤖 WCA AI Agent")
    st.caption("Powered by Gemini 2.0 Flash on Vertex AI · Live MongoDB tool calling")

    # Service account + model status banner
    if not os.path.exists(SA_KEY_PATH):
        st.warning(
            f"⚠️ **Service account key missing** — place `service_account.json` in your project "
            f"folder to enable the AI agent.\n\n"
            f"GCP Console → IAM & Admin → Service Accounts → "
            f"`worldcup-fantasy-agent@appspot.gserviceaccount.com` → Keys → Add Key → JSON"
        )
    else:
        _, ok, info = init_vertex()
        if ok:
            st.success(f"✅ {info}")
        else:
            st.error(f"❌ Vertex AI: {info}")

    # Init chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hi! I'm WCA, your World Cup Fantasy Agent running on **Vertex AI (Gemini 2.0 Flash)**. "
                    "I can show you matches, create leagues, and save predictions. What would you like to do?"
                ),
            }
        ]

    # Quick prompt buttons
    st.markdown("**Quick prompts:**")
    qcols = st.columns(4)
    prompts = [
        "Show me 5 matches",
        "Create a league for 10 friends",
        "Predict Argentina vs Brazil 2-1",
        "Show database stats",
    ]
    for i, (col, prompt) in enumerate(zip(qcols, prompts)):
        if col.button(prompt, key=f"qp_{i}"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("⚽ Thinking..."):
                reply = call_vertex_agent(prompt, st.session_state.chat_history[:-1])
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    st.divider()

    # Chat display
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="⚽"):
                st.write(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask anything about World Cup 2026…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("⚽ Thinking..."):
            reply = call_vertex_agent(user_input, st.session_state.chat_history[:-1])
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Chat cleared! How can I help you?"}
        ]
        st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#3a4a6a;font-size:12px'>"
    "WorldCup Fantasy Agent · Google Cloud Rapid Agent Hackathon 2026 · "
    "Streamlit · MongoDB Atlas · Vertex AI (Gemini 2.0 Flash)"
    "</p>",
    unsafe_allow_html=True,
)
