"""
streamlit_app.py — MandiMind Streamlit Application

A complete conversion of the MandiMind React+FastAPI stack into a single
Streamlit app that can be deployed directly on Streamlit Community Cloud.

Architecture:
    - All backend logic is imported directly (no HTTP round-trips)
    - Streamlit handles the full UI (form, results, tables, AI reply)
    - Session state manages conversation history + results
"""

from __future__ import annotations

import sys
import os

# ── Ensure the project root is on sys.path so backend imports resolve ──────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
import pandas as pd

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="MandiMind — Find Your Best Mandi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject custom CSS for a premium look ──────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }

    /* ── Hide Streamlit chrome ──────────────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 4rem; }

    /* ── Header banner ──────────────────────────────────────────────── */
    .mm-header {
        background: linear-gradient(135deg, #1a2e1a 0%, #0f2027 60%, #1a2e1a 100%);
        border: 1px solid rgba(46, 160, 67, 0.3);
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 8px 32px rgba(46, 160, 67, 0.08);
    }
    .mm-logo { font-size: 2.6rem; line-height: 1; }
    .mm-title { font-size: 1.9rem; font-weight: 800; color: #3fb950; letter-spacing: -0.5px; margin: 0; }
    .mm-subtitle { font-size: 0.88rem; color: #8b949e; margin: 4px 0 0; }

    /* ── Metric cards ───────────────────────────────────────────────── */
    .metric-grid { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
    .metric-card {
        flex: 1; min-width: 160px;
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        transition: border-color 0.2s, transform 0.2s;
    }
    .metric-card:hover { border-color: rgba(46, 160, 67, 0.5); transform: translateY(-2px); }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #3fb950; }
    .metric-label { font-size: 0.78rem; color: #8b949e; margin-top: 4px; letter-spacing: 0.5px; text-transform: uppercase; }

    /* ── Top recommendation card ────────────────────────────────────── */
    .top-card {
        background: linear-gradient(135deg, rgba(46,160,67,0.12) 0%, rgba(22,27,34,0.95) 100%);
        border: 1px solid rgba(46, 160, 67, 0.4);
        border-radius: 16px;
        padding: 28px 32px;
        margin: 20px 0;
        box-shadow: 0 4px 24px rgba(46, 160, 67, 0.10);
    }
    .top-card-badge {
        display: inline-block;
        background: linear-gradient(90deg, #238636, #2ea043);
        color: #fff;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 99px;
        margin-bottom: 12px;
    }
    .top-card-market { font-size: 1.7rem; font-weight: 800; color: #e6edf3; margin: 0; }
    .top-card-district { font-size: 1rem; color: #8b949e; margin: 4px 0 0; }

    /* ── AI reply box ───────────────────────────────────────────────── */
    .ai-reply-box {
        background: rgba(22, 27, 34, 0.85);
        border: 1px solid rgba(88, 166, 255, 0.25);
        border-left: 4px solid #58a6ff;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 20px 0;
        line-height: 1.65;
        color: #c9d1d9;
    }
    .ai-label {
        font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; color: #58a6ff; margin-bottom: 10px;
    }

    /* ── Section headings ───────────────────────────────────────────── */
    .section-heading {
        font-size: 1rem; font-weight: 700; color: #c9d1d9;
        letter-spacing: 0.3px; margin: 24px 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(48, 54, 61, 0.8);
    }

    /* ── Warning / info banners ─────────────────────────────────────── */
    .banner-warn {
        background: rgba(210, 153, 34, 0.08);
        border: 1px solid rgba(210, 153, 34, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        color: #e3b341;
        font-size: 0.88rem;
        margin: 12px 0;
    }
    .banner-info {
        background: rgba(88, 166, 255, 0.06);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 10px;
        padding: 14px 18px;
        color: #8b949e;
        font-size: 0.82rem;
        margin: 12px 0;
    }

    /* ── Streamlit form elements ────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: rgba(22, 27, 34, 0.9) !important;
        border: 1px solid rgba(48, 54, 61, 0.9) !important;
        color: #e6edf3 !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: rgba(46, 160, 67, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(46, 160, 67, 0.12) !important;
    }

    /* ── Primary button ─────────────────────────────────────────────── */
    div.stButton > button[kind="primary"],
    div.stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        padding: 0.6rem 1.8rem !important;
        font-size: 1rem !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(46, 160, 67, 0.35) !important;
    }

    /* ── Dataframe styling ──────────────────────────────────────────── */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* ── Progress steps ─────────────────────────────────────────────── */
    .step-row { display: flex; align-items: center; gap: 12px; padding: 7px 0; }
    .step-icon { font-size: 1.05rem; width: 22px; text-align: center; }
    .step-label { font-size: 0.88rem; color: #8b949e; }
    .step-label.done { color: #3fb950; }
    .step-label.active { color: #e6edf3; font-weight: 600; }
    .step-label.error { color: #f85149; }

    /* ── Chat ───────────────────────────────────────────────────────── */
    .chat-msg { padding: 10px 16px; border-radius: 10px; margin: 6px 0; font-size: 0.9rem; }
    .chat-user { background: rgba(46,160,67,0.1); border: 1px solid rgba(46,160,67,0.2); text-align: right; }
    .chat-bot { background: rgba(88,166,255,0.06); border: 1px solid rgba(88,166,255,0.15); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Lazy-import backend ────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _load_backend():
    try:
        from backend.agent.gemma_agent import chat as agent_chat
        from backend.services.pipeline import rank_market_options
        from backend.tools.mandi_prices import get_mandi_prices
        return agent_chat, rank_market_options, get_mandi_prices, None
    except ImportError as exc:
        return None, None, None, str(exc)


agent_chat, rank_market_options, get_mandi_prices, _import_err = _load_backend()

# ── Constants ──────────────────────────────────────────────────────────────
STATES = [
    "Uttar Pradesh", "Madhya Pradesh", "Punjab", "Haryana",
    "Rajasthan", "Bihar", "Maharashtra", "Gujarat", "Andhra Pradesh",
    "Karnataka", "Telangana", "West Bengal", "Odisha", "Chhattisgarh",
]

CROPS = [
    "Wheat", "Potato", "Tomato", "Onion", "Rice", "Maize",
    "Soybean", "Mustard", "Barley", "Jowar", "Bajra", "Cotton", "Sugarcane",
]

STEPS = [
    ("understanding",  "🧠", "Understanding your query"),
    ("prices",         "📊", "Fetching live mandi prices"),
    ("fallback",       "🔄", "State-wide price fallback"),
    ("locations",      "📍", "Resolving market locations"),
    ("distance",       "📏", "Calculating distances"),
    ("transport",      "🚛", "Estimating transport costs"),
    ("returns",        "💰", "Computing net returns"),
    ("recommendation", "⭐", "Generating AI recommendation"),
]


# ── Session state init ─────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "result": None,
        "reply": "",
        "tool_calls": [],
        "error": None,
        "show_steps": False,
        "step_states": {},
        "history": [],
        "last_query": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ── Helper: render step list ───────────────────────────────────────────────
def _render_steps(step_states: dict):
    for key, icon, label in STEPS:
        st_val = step_states.get(key, "pending")
        if st_val == "skipped":
            continue
        if st_val == "done":
            st.markdown(
                f'<div class="step-row"><span class="step-icon">✅</span>'
                f'<span class="step-label done">{label}</span></div>',
                unsafe_allow_html=True,
            )
        elif st_val == "active":
            st.markdown(
                f'<div class="step-row"><span class="step-icon">⏳</span>'
                f'<span class="step-label active">{label}…</span></div>',
                unsafe_allow_html=True,
            )
        elif st_val == "error":
            st.markdown(
                f'<div class="step-row"><span class="step-icon">❌</span>'
                f'<span class="step-label error">{label}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="step-row"><span class="step-icon">⬜</span>'
                f'<span class="step-label">{label}</span></div>',
                unsafe_allow_html=True,
            )


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="mm-header">
        <div class="mm-logo">🌾</div>
        <div>
            <div class="mm-title">MandiMind</div>
            <div class="mm-subtitle">
                Real Government mandi prices &nbsp;·&nbsp;
                Gemma 4 AI reasoning &nbsp;·&nbsp;
                Transport-adjusted net return comparison
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Backend error guard ────────────────────────────────────────────────────
if _import_err:
    st.error(
        f"**Could not load backend modules.**\n\n"
        f"Make sure you run the app from the project root:\n"
        f"```\nstreamlit run streamlit_app.py\n```\n\n"
        f"Error: `{_import_err}`"
    )
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_market, tab_chat, tab_prices = st.tabs(
    ["🏆 Market Finder", "💬 AI Chat", "📋 Price Lookup"]
)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Market Finder
# ═══════════════════════════════════════════════════════════════════════════
with tab_market:

    col_form, col_results = st.columns([1, 1.6], gap="large")

    # ── Left: Query Form ──────────────────────────────────────────────────
    with col_form:
        st.markdown('<div class="section-heading">🌾 Your Crop Details</div>', unsafe_allow_html=True)

        with st.form("market_finder_form", clear_on_submit=False):
            location = st.text_input(
                "Your Location (City / District)",
                placeholder="e.g. Prayagraj, Lucknow, Agra…",
                help="Enter your city or district name.",
            )

            state = st.selectbox("State", options=STATES, index=0)
            commodity = st.selectbox("Crop / Commodity", options=CROPS, index=0)

            col_qty, col_rad = st.columns(2)
            with col_qty:
                quantity = st.number_input(
                    "Quantity (Quintals)", min_value=1.0, max_value=10000.0,
                    value=100.0, step=10.0,
                )
            with col_rad:
                radius = st.number_input(
                    "Search Radius (km)", min_value=10.0, max_value=500.0,
                    value=150.0, step=10.0,
                )

            submitted = st.form_submit_button("🔍 Find Best Mandi", use_container_width=True)

        # Progress steps
        if st.session_state.show_steps:
            st.markdown('<div class="section-heading">⚡ Processing Steps</div>', unsafe_allow_html=True)
            _render_steps(st.session_state.step_states)

        # Search summary metrics
        result = st.session_state.result
        if result and result.get("status") == "ok":
            st.markdown('<div class="section-heading">📊 Search Summary</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="metric-grid">'
                f'<div class="metric-card"><div class="metric-value">{result.get("candidates_in_radius", 0)}</div>'
                f'<div class="metric-label">Markets Found</div></div>'
                f'<div class="metric-card"><div class="metric-value">{result.get("total_api_records", 0)}</div>'
                f'<div class="metric-label">API Records</div></div>'
                f'<div class="metric-card"><div class="metric-value">{result.get("search_radius_km", 150):.0f} km</div>'
                f'<div class="metric-label">Search Radius</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if result.get("state_wide_fallback_used"):
                st.markdown(
                    '<div class="banner-warn">⚠️ No local listings found — state-wide price data used instead.</div>',
                    unsafe_allow_html=True,
                )

    # ── Right: Results ────────────────────────────────────────────────────
    with col_results:

        # Handle form submission
        if submitted:
            if not location.strip():
                st.error("Please enter your location.")
            else:
                # Reset state
                st.session_state.result = None
                st.session_state.reply = ""
                st.session_state.tool_calls = []
                st.session_state.error = None
                st.session_state.show_steps = True
                st.session_state.last_query = {
                    "location": location, "state": state,
                    "commodity": commodity, "quantity_quintals": quantity,
                    "search_radius_km": radius,
                }

                step_states = {k: "pending" for k, _, _ in STEPS}
                step_states["fallback"] = "skipped"
                st.session_state.step_states = step_states

                user_message = (
                    f"I have {quantity} quintals of {commodity} "
                    f"and I am in {location}, {state}. "
                    f"Please find the best market to sell within {radius:.0f} km."
                )

                with st.spinner("🤖 MandiMind is analysing your query…"):
                    try:
                        agent_result = agent_chat(user_message=user_message, history=[])

                        step_states["understanding"] = "done"
                        step_states["prices"] = "done"

                        pipeline_result = agent_result.pipeline_result
                        if pipeline_result:
                            if pipeline_result.get("state_wide_fallback_used"):
                                step_states["fallback"] = "done"
                            step_states["locations"] = "done"
                            step_states["distance"] = "done"
                            step_states["transport"] = "done"
                            step_states["returns"] = "done"

                        step_states["recommendation"] = "done"
                        st.session_state.step_states = step_states
                        st.session_state.result = pipeline_result
                        st.session_state.reply = agent_result.reply
                        st.session_state.tool_calls = agent_result.tool_calls_made

                    except Exception as exc:
                        st.session_state.error = str(exc)
                        for k in step_states:
                            if step_states[k] == "active":
                                step_states[k] = "error"
                        st.session_state.step_states = step_states

                st.rerun()

        # Error display
        if st.session_state.error:
            st.error(f"⚠️ **Error:** {st.session_state.error}")

        result = st.session_state.result

        # Empty state
        if result is None and not st.session_state.error and not submitted:
            st.markdown(
                """
                <div style="text-align:center; padding: 60px 20px; color: #8b949e;">
                    <div style="font-size: 4rem; margin-bottom: 16px;">🌾</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #c9d1d9; margin-bottom: 8px;">Ready to Analyse</div>
                    <div style="font-size: 0.9rem; line-height: 1.6;">
                        Enter your location, crop, and quantity on the left.<br>
                        Gemma 4 AI will find your best estimated net return across nearby mandis.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif result and result.get("status") in ("no_results", "error"):
            st.warning(f"⚠️ {result.get('message', 'No markets found.')}")
            st.info("💡 Try increasing the search radius or check the commodity name.")

        elif result and result.get("status") == "ok":
            top = result.get("top_recommendation", {})

            if top:
                net_return = top.get("estimated_net_return", 0)
                transport = top.get("estimated_transport_cost", 0)
                dist = top.get("distance_km", 0)
                modal = top.get("modal_price", 0)

                st.markdown(
                    f"""
                    <div class="top-card">
                        <div class="top-card-badge">⭐ Top Recommendation</div>
                        <div class="top-card-market">{top.get("market", "—")}</div>
                        <div class="top-card-district">{top.get("district", "—")} · {top.get("state", "—")}</div>
                        <div class="metric-grid" style="margin-top:20px;">
                            <div class="metric-card">
                                <div class="metric-value">₹{net_return:,.0f}</div>
                                <div class="metric-label">Est. Net Return</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">₹{modal:,.0f}</div>
                                <div class="metric-label">Modal Price / Q</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{dist:.1f} km</div>
                                <div class="metric-label">Distance</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">₹{transport:,.0f}</div>
                                <div class="metric-label">Transport Cost</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # AI reply
            if st.session_state.reply:
                st.markdown(
                    f"""
                    <div class="ai-reply-box">
                        <div class="ai-label">🤖 Gemma 4 Recommendation</div>
                        {st.session_state.reply}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Comparison table
            ranked = result.get("ranked_markets", [])
            if ranked:
                st.markdown(
                    '<div class="section-heading">📊 Market Comparison Table</div>',
                    unsafe_allow_html=True,
                )

                df = pd.DataFrame(ranked)
                cols_available = [c for c in [
                    "market", "district", "modal_price", "min_price", "max_price",
                    "distance_km", "estimated_transport_cost", "estimated_net_return",
                ] if c in df.columns]
                df = df[cols_available].rename(columns={
                    "market": "Market", "district": "District",
                    "modal_price": "Modal ₹/Q", "min_price": "Min ₹/Q", "max_price": "Max ₹/Q",
                    "distance_km": "Dist (km)", "estimated_transport_cost": "Transport ₹",
                    "estimated_net_return": "Net Return ₹",
                })

                for col in ["Modal ₹/Q", "Min ₹/Q", "Max ₹/Q"]:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"₹{x:,.0f}" if x is not None else "—")
                if "Dist (km)" in df.columns:
                    df["Dist (km)"] = df["Dist (km)"].apply(
                        lambda x: f"{x:.1f}" if x is not None else "—"
                    )
                for col in ["Transport ₹", "Net Return ₹"]:
                    if col in df.columns:
                        df[col] = df[col].apply(
                            lambda x: f"₹{x:,.0f}" if x is not None else "—"
                        )

                st.dataframe(df, use_container_width=True, hide_index=True,
                             height=min(38 + len(df) * 35, 400))

            # Transparency expander
            with st.expander("🔍 Pipeline Transparency", expanded=False):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown(f"**Origin:** `{result.get('origin', '—')}`")
                    oc = result.get("origin_coordinates") or {}
                    if oc:
                        st.markdown(f"**Coordinates:** `{oc.get('lat',0):.4f}°N, {oc.get('lon',0):.4f}°E`")
                    st.markdown(f"**Local search:** `{result.get('local_search_attempted')}`")
                    st.markdown(f"**Local records:** `{result.get('local_records_found', 0)}`")
                with col_t2:
                    st.markdown(f"**State-wide fallback:** `{result.get('state_wide_fallback_used')}`")
                    st.markdown(f"**Total API records:** `{result.get('total_api_records', 0)}`")
                    st.markdown(f"**Candidates in radius:** `{result.get('candidates_in_radius', 0)}`")
                    st.markdown(f"**Search radius:** `{result.get('search_radius_km', 150):.0f} km`")

                tn = result.get("transport_note", "")
                if tn:
                    st.markdown(f'<div class="banner-info">ℹ️ {tn}</div>', unsafe_allow_html=True)

                if st.session_state.tool_calls:
                    st.markdown("**Tools called:** " + ", ".join(f"`{t}`" for t in st.session_state.tool_calls))

            # Data provenance
            st.markdown(
                """
                <div class="banner-info">
                    📡 <b>Data source:</b> Government of India Open Data Platform (data.gov.in) ·
                    Ministry of Agriculture &amp; Farmers Welfare ·
                    <a href="https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
                       style="color:#58a6ff;" target="_blank">Dataset link</a>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — AI Chat
# ═══════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown('<div class="section-heading">💬 Chat with MandiMind AI</div>', unsafe_allow_html=True)
    st.caption("Ask anything in **English or Hindi** about selling your crop.")

    for msg in st.session_state.history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        css_cls = "chat-user" if role == "user" else "chat-bot"
        icon = "👨‍🌾" if role == "user" else "🤖"
        st.markdown(
            f'<div class="chat-msg {css_cls}">{icon} {content}</div>',
            unsafe_allow_html=True,
        )

    chat_input = st.chat_input(
        "e.g. 'I have 200 quintals of wheat in Prayagraj, where should I sell?'"
    )

    if chat_input:
        st.session_state.history.append({"role": "user", "content": chat_input})
        with st.spinner("MandiMind is thinking…"):
            try:
                agent_result = agent_chat(user_message=chat_input, history=[])
                bot_reply = agent_result.reply
                pr = agent_result.pipeline_result
                if pr and pr.get("status") == "ok":
                    top = pr.get("top_recommendation", {})
                    if top:
                        bot_reply += (
                            f"\n\n📍 **Top pick:** {top.get('market')} ({top.get('district')}) — "
                            f"₹{top.get('modal_price',0):,.0f}/Q · "
                            f"{top.get('distance_km',0):.1f} km · "
                            f"Net Return ₹{top.get('estimated_net_return',0):,.0f}"
                        )
            except Exception as exc:
                bot_reply = f"Sorry, I encountered an error: {exc}"

        st.session_state.history.append({"role": "assistant", "content": bot_reply})
        st.rerun()

    if st.session_state.history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Price Lookup
# ═══════════════════════════════════════════════════════════════════════════
with tab_prices:
    st.markdown('<div class="section-heading">📋 Direct Mandi Price Lookup</div>', unsafe_allow_html=True)
    st.caption("Look up current government mandi prices for any commodity in any state.")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        p_state = st.selectbox("State", options=STATES, key="price_state")
    with col_p2:
        p_commodity = st.selectbox("Commodity", options=CROPS, key="price_commodity")
    with col_p3:
        p_district = st.text_input("District (optional)", placeholder="e.g. Prayagraj", key="price_district")

    if st.button("🔍 Fetch Prices", key="price_fetch"):
        with st.spinner("Fetching live prices from data.gov.in…"):
            try:
                price_result = get_mandi_prices(
                    state=p_state,
                    commodity=p_commodity,
                    district=p_district.strip() or None,
                    limit=100,
                )

                if price_result["status"] == "ok":
                    records = price_result.get("records", [])
                    st.success(f"✅ Found **{price_result['total']}** record(s).")

                    wanted_cols = ["market", "district", "state", "commodity", "variety",
                                   "modal_price", "min_price", "max_price", "arrival_date"]
                    df_prices = pd.DataFrame(records)
                    df_prices = df_prices[[c for c in wanted_cols if c in df_prices.columns]]
                    df_prices = df_prices.rename(columns={
                        "market": "Market", "district": "District", "state": "State",
                        "commodity": "Commodity", "variety": "Variety",
                        "modal_price": "Modal ₹/Q", "min_price": "Min ₹/Q",
                        "max_price": "Max ₹/Q", "arrival_date": "Date",
                    })
                    for col in ["Modal ₹/Q", "Min ₹/Q", "Max ₹/Q"]:
                        if col in df_prices.columns:
                            df_prices[col] = df_prices[col].apply(lambda x: f"₹{x:,.0f}")

                    st.dataframe(df_prices, use_container_width=True, hide_index=True)

                    raw_modal = [r["modal_price"] for r in records if r.get("modal_price")]
                    if raw_modal:
                        st.markdown(
                            f'<div class="metric-grid">'
                            f'<div class="metric-card"><div class="metric-value">₹{min(raw_modal):,.0f}</div><div class="metric-label">Min Modal Price</div></div>'
                            f'<div class="metric-card"><div class="metric-value">₹{max(raw_modal):,.0f}</div><div class="metric-label">Max Modal Price</div></div>'
                            f'<div class="metric-card"><div class="metric-value">₹{sum(raw_modal)/len(raw_modal):,.0f}</div><div class="metric-label">Avg Modal Price</div></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                elif price_result["status"] == "no_results":
                    st.warning(f"⚠️ {price_result['message']}")
                else:
                    st.error(f"❌ {price_result['message']}")

            except Exception as exc:
                st.error(f"Error fetching prices: {exc}")


# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; color:#484f58; font-size:0.78rem; margin-top:40px; padding-top:20px;
                border-top: 1px solid rgba(48,54,61,0.5);">
        MandiMind &nbsp;·&nbsp; Built for Indian Farmers &nbsp;·&nbsp;
        Powered by Gemma 4 &amp; Government of India Open Data &nbsp;·&nbsp;
        <em>Transport costs are estimates — not official government rates.</em>
    </div>
    """,
    unsafe_allow_html=True,
)
