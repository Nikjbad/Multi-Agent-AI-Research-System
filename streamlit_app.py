"""
Streamlit UI for the multi-agent research pipeline (pipeline.py / agents.py).

Run with:
    streamlit run streamlit_app.py

Place this file in the same folder as agents.py and tools.py.
"""

import time
import re
import html
import traceback

import streamlit as st

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Research Agent Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# Global CSS - white background, Google-Ads-style palette, light motion accents
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

:root{
    --blue:#1a73e8;
    --blue-dark:#0b57d0;
    --green:#34a853;
    --yellow:#fbbc04;
    --red:#ea4335;
    --ink:#202124;
    --muted:#5f6368;
    --card:#ffffff;
    --border:#e8eaed;
}

html, body, [class*="css"]{
    font-family: 'Roboto', 'Google Sans', Arial, sans-serif;
}

/* ---- force light look, even if the user's Streamlit is in dark mode ---- */
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
.stApp{
    background:
        radial-gradient(circle at 12% 8%, rgba(26,115,232,0.07), transparent 40%),
        radial-gradient(circle at 88% 15%, rgba(52,168,83,0.07), transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(251,188,4,0.06), transparent 45%),
        #ffffff !important;
    color: var(--ink) !important;
    overflow-x: hidden;
}
[data-testid="stHeader"]{ background: transparent !important; }

[data-testid="stSidebar"]{ background: #f8f9fa !important; }
[data-testid="stSidebar"] *{ color: var(--ink) !important; }

.stApp p, .stApp li, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4{
    color: var(--ink);
}

/* content sits above the blobs */
.block-container{ position: relative; z-index: 1; }

/* floating animated blobs behind everything */
.blob{
    position: fixed;
    border-radius: 50%;
    filter: blur(60px);
    opacity: 0.30;
    z-index: -1 !important;
    pointer-events: none;
    animation: float 14s ease-in-out infinite;
}
.blob1{ width:320px; height:320px; top:-80px; left:-100px;
    background: radial-gradient(circle, var(--blue), transparent 70%); }
.blob2{ width:260px; height:260px; top:40%; right:-100px;
    background: radial-gradient(circle, var(--green), transparent 70%);
    animation-delay: 3s; }
.blob3{ width:220px; height:220px; bottom:-80px; left:30%;
    background: radial-gradient(circle, var(--yellow), transparent 70%);
    animation-delay: 6s; }

@keyframes float{
    0%,100%{ transform: translate(0,0) scale(1); }
    50%{ transform: translate(20px,-30px) scale(1.08); }
}
@keyframes fadeInUp{
    from{ opacity:0; transform: translateY(24px); }
    to{ opacity:1; transform: translateY(0); }
}
@keyframes pulseDot{
    0%,100%{ transform: scale(1); box-shadow:0 0 0 0 rgba(26,115,232,0.45); }
    50%{ transform: scale(1.15); box-shadow:0 0 0 8px rgba(26,115,232,0); }
}

/* hero */
.hero{
    position: relative;
    z-index: 1;
    text-align:center;
    padding: 2.6rem 1rem 1.6rem 1rem;
    animation: fadeInUp 0.7s ease both;
}
.hero .badge{
    display:inline-block;
    padding: 6px 16px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(26,115,232,0.1), rgba(52,168,83,0.1));
    color: var(--blue-dark);
    font-weight:500;
    font-size:0.8rem;
    letter-spacing:0.04em;
    margin-bottom: 14px;
}
.hero h1{
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight:700;
    color: var(--ink) !important;
    margin: 0;
    line-height:1.15;
}
.hero h1 span{
    background: linear-gradient(90deg, var(--blue), var(--green) 60%, var(--yellow));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero p{
    color: var(--muted) !important;
    font-size: clamp(0.95rem, 2vw, 1.1rem);
    max-width: 620px;
    margin: 14px auto 0 auto;
}

/* card (no 3D rotate - it made text blurry) */
.card{
    position: relative;
    z-index: 1;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 1px 2px rgba(60,64,67,0.08), 0 6px 20px rgba(60,64,67,0.06);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: fadeInUp 0.6s ease both;
    margin-bottom: 1rem;
}
.card:hover{
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(60,64,67,0.14), 0 2px 6px rgba(60,64,67,0.08);
}

/* step tracker */
.steps{
    display:flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content:center;
    margin: 1.4rem 0 1.8rem 0;
    position: relative;
    z-index:1;
}
.step{
    display:flex;
    align-items:center;
    gap:8px;
    padding: 10px 16px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: #fff;
    font-size: 0.85rem;
    font-weight:500;
    color: var(--muted);
    transition: all 0.4s ease;
}
.step.active{
    border-color: var(--blue);
    color: var(--blue-dark);
    box-shadow: 0 4px 14px rgba(26,115,232,0.18);
    transform: translateY(-2px) scale(1.03);
}
.step.done{
    border-color: var(--green);
    color: #1e7e34;
    background: rgba(52,168,83,0.06);
}
.dot{
    width:8px; height:8px; border-radius:50%;
    background: var(--border);
}
.step.active .dot{
    background: var(--blue);
    animation: pulseDot 1.4s infinite;
}
.step.done .dot{ background: var(--green); }

/* section title inside cards */
.section-title{
    display:flex;
    align-items:center;
    gap:10px;
    font-weight:700;
    color: var(--ink);
    font-size:1.05rem;
    margin-bottom: 0.6rem;
}
.section-title .chip{
    width:30px; height:30px;
    border-radius: 9px;
    display:flex; align-items:center; justify-content:center;
    font-size:1rem;
    color:#fff;
}

/* result text box */
.content-box{
    max-height: 340px;
    overflow-y: auto;
    padding-right: 6px;
    color: var(--ink);
    font-size: 0.92rem;
    line-height:1.6;
    word-wrap: break-word;
    overflow-wrap: anywhere;
    -webkit-font-smoothing: antialiased;
}
.content-box p{ margin: 0 0 0.7em 0; color: var(--ink); }
.content-box p:last-child{ margin-bottom: 0; }
.content-box ul, .content-box ol{
    margin: 0 0 0.7em 1.3em;
    padding: 0;
}
.content-box li{ margin-bottom: 0.3em; color: var(--ink); }
.content-box h4, .content-box h5, .content-box h6{
    margin: 0.9em 0 0.4em 0;
    color: var(--ink);
    font-weight: 700;
}
.content-box h4:first-child,
.content-box h5:first-child,
.content-box h6:first-child{ margin-top: 0; }
.content-box strong{ color: var(--ink); }
.content-box hr{
    border: none;
    border-top: 1px solid var(--border);
    margin: 0.9em 0;
}

/* CTA button */
div.stButton > button{
    background: linear-gradient(90deg, var(--blue), var(--blue-dark));
    color: #fff;
    border: none;
    border-radius: 999px;
    padding: 0.65rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    box-shadow: 0 6px 18px rgba(26,115,232,0.35);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    width: 100%;
}
div.stButton > button:hover{
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 10px 26px rgba(26,115,232,0.45);
    color: #fff;
    border: none;
}
div.stButton > button:active{ transform: translateY(0) scale(0.99); }
div.stButton > button p,
div.stDownloadButton > button p{ color: #fff !important; }

div.stDownloadButton > button{
    background: linear-gradient(90deg, var(--green), #2d8f47);
    color: #fff;
    border: none;
    border-radius: 999px;
    padding: 0.65rem 2rem;
    font-weight: 600;
}

/* text input */
.stTextInput > div > div > input{
    border-radius: 14px;
    border: 1.5px solid var(--border);
    padding: 0.7rem 1rem;
    font-size: 1rem;
    color: var(--ink) !important;
    background: #fff !important;
    -webkit-text-fill-color: var(--ink) !important;
}
.stTextInput > div > div > input::placeholder{
    color: var(--muted) !important;
    -webkit-text-fill-color: var(--muted) !important;
    opacity: 1;
}
.stTextInput > div > div > input:focus{
    border-color: var(--blue);
    box-shadow: 0 0 0 3px rgba(26,115,232,0.15);
}
.stTextInput > div > div{ background: #fff !important; }

/* spinner + alerts */
[data-testid="stSpinner"] *{ color: var(--ink) !important; }
[data-testid="stAlert"] *{ color: var(--ink) !important; }

.footer-note{
    text-align:center;
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 2rem;
    padding-bottom: 2rem;
    position:relative;
    z-index:1;
}

/* "how it works" agent grid */
.agent-grid{
    display:grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    max-width: 1000px;
    margin: 0 auto 1.6rem auto;
    position:relative;
    z-index:1;
}
@media (max-width: 900px){
    .agent-grid{ grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px){
    .agent-grid{ grid-template-columns: 1fr; }
}
.agent-card{
    background:#fff;
    border:1px solid var(--border);
    border-radius:16px;
    padding: 1.1rem 1rem;
    text-align:left;
    box-shadow: 0 1px 2px rgba(60,64,67,0.06);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: fadeInUp 0.6s ease both;
}
.agent-card:hover{
    transform: translateY(-5px);
    box-shadow: 0 12px 26px rgba(60,64,67,0.14);
}
.agent-card .num{
    display:inline-flex;
    align-items:center; justify-content:center;
    width:26px; height:26px;
    border-radius:50%;
    font-size:0.75rem; font-weight:700;
    color:#fff;
    margin-bottom:8px;
}
.agent-card h4{
    margin: 4px 0 4px 0;
    font-size:0.98rem;
    color: var(--ink) !important;
}
.agent-card p{
    margin:0;
    font-size:0.82rem;
    color: var(--muted) !important;
    line-height:1.45;
}

/* meta badges on result cards */
.meta-row{
    display:flex;
    gap:8px;
    margin: -4px 0 10px 0;
    flex-wrap:wrap;
}
.meta-badge{
    font-size:0.72rem;
    font-weight:500;
    color: var(--muted);
    background: #f1f3f4;
    border-radius: 999px;
    padding: 3px 10px;
}

/* mobile */
@media (max-width: 640px){
    .card{ padding: 1.1rem 1.1rem; border-radius: 14px; }
    .steps{ gap:6px; }
    .step{ padding: 8px 12px; font-size:0.75rem; }
    .content-box{ max-height: 260px; font-size:0.85rem; }
}
</style>

<div class="blob blob1"></div>
<div class="blob blob2"></div>
<div class="blob blob3"></div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = {}
if "running" not in st.session_state:
    st.session_state.running = False
if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 0=idle,1=search,2=read,3=write,4=critique,5=done

STEP_LABELS = ["Search", "Read", "Write", "Critique"]

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="badge">MULTI-AGENT RESEARCH PIPELINE</div>
        <h1>Turn any topic into a <span>researched report</span></h1>
        <p>Four AI agents search, read, write, and critique — end to end,
        right in your browser.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# "How it works" - informative agent overview
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="agent-grid">
        <div class="agent-card">
            <div class="num" style="background:linear-gradient(135deg,#1a73e8,#4285f4);">1</div>
            <h4>🔎 Search Agent</h4>
            <p>Queries the web for recent, reliable sources on your topic and
            summarizes what it finds.</p>
        </div>
        <div class="agent-card">
            <div class="num" style="background:linear-gradient(135deg,#34a853,#66bb6a);">2</div>
            <h4>📄 Reader Agent</h4>
            <p>Picks the most relevant link from those results and scrapes it
            for deeper, first-hand detail.</p>
        </div>
        <div class="agent-card">
            <div class="num" style="background:linear-gradient(135deg,#fbbc04,#f9a825);">3</div>
            <h4>✍️ Writer Chain</h4>
            <p>Combines the search summary and scraped content into a single,
            structured research report.</p>
        </div>
        <div class="agent-card">
            <div class="num" style="background:linear-gradient(135deg,#ea4335,#ff7043);">4</div>
            <h4>🧐 Critic Chain</h4>
            <p>Reviews the draft report for gaps, bias, or weak evidence and
            returns actionable feedback.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Sidebar - project info
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📘 About this project")
    st.markdown(
        """
This app is a **UI layer** over a multi-agent research pipeline
(`pipeline.py` / `agents.py`).

**Pipeline flow**
1. `build_search_agent()` — searches the web
2. `build_reader_agent()` — scrapes the top result
3. `writer_chain` — drafts a report from steps 1–2
4. `critic_chain` — reviews the draft report

**Stack**
- Python + LangChain agents
- Streamlit for the interface
        """
    )
    st.divider()
    st.caption("Enter a topic and click **Start Research** to run all four agents in sequence.")

# ----------------------------------------------------------------------------
# Input card
# ----------------------------------------------------------------------------
col_l, col_c, col_r = st.columns([1, 3, 1])
with col_c:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    topic = st.text_input(
        "Research topic",
        placeholder="e.g. The impact of quantum computing on cryptography",
        label_visibility="collapsed",
        key="topic_input",
    )
    start = st.button("🚀  Start Research", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def render_steps(current: int):
    """current: 0 idle, 1..4 = which step is active, 5 = all done"""
    out = '<div class="steps">'
    for i, label in enumerate(STEP_LABELS, start=1):
        cls = ""
        if current > i or current == 5:
            cls = "done"
        elif current == i:
            cls = "active"
        out += f'<div class="step {cls}"><span class="dot"></span>{label}</div>'
    out += "</div>"
    st.markdown(out, unsafe_allow_html=True)


def normalize_content(raw) -> str:
    """LLM content can be a plain string OR a list of blocks. Handle both."""
    if raw is None:
        return ""
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "\n".join(p for p in parts if p)
    return str(raw)


def _inline_format(segment: str) -> str:
    """Escape HTML, then apply **bold** / *italic* inline formatting."""
    segment = html.escape(segment)
    segment = segment.replace("$", "&#36;")  # stop Streamlit treating $...$ as LaTeX
    segment = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", segment)
    segment = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", segment)
    return segment


def format_agent_text(raw) -> str:
    """
    Turn raw agent/LLM text (inconsistent blank lines, light markdown)
    into clean, evenly-spaced HTML.
    """
    text = normalize_content(raw).strip()
    if not text:
        return "<p><em>No content returned.</em></p>"

    # normalize excessive blank lines / trailing spaces
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)

    parts, para_buf, list_buf, list_tag = [], [], [], None

    def flush_paragraph():
        if para_buf:
            joined = " ".join(s.strip() for s in para_buf if s.strip())
            if joined:
                parts.append(f"<p>{_inline_format(joined)}</p>")
            para_buf.clear()

    def flush_list():
        nonlocal list_tag
        if list_buf:
            items = "".join(f"<li>{_inline_format(i)}</li>" for i in list_buf)
            parts.append(f"<{list_tag}>{items}</{list_tag}>")
            list_buf.clear()
            list_tag = None

    for line in text.split("\n"):
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        # horizontal rule: ---, ***, ___
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush_paragraph()
            flush_list()
            parts.append("<hr>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)", stripped)
        bullet = re.match(r"^[-*•]\s+(.*)", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.*)", stripped)

        if heading:
            flush_paragraph()
            flush_list()
            tag = {1: "h4", 2: "h5"}.get(len(heading.group(1)), "h6")
            parts.append(f"<{tag}>{_inline_format(heading.group(2))}</{tag}>")
            continue
        if bullet:
            flush_paragraph()
            if list_tag != "ul":
                flush_list()
                list_tag = "ul"
            list_buf.append(bullet.group(1))
            continue
        if numbered:
            flush_paragraph()
            if list_tag != "ol":
                flush_list()
                list_tag = "ol"
            list_buf.append(numbered.group(1))
            continue

        flush_list()
        para_buf.append(stripped)

    flush_paragraph()
    flush_list()

    return "".join(parts) if parts else f"<p>{_inline_format(text)}</p>"


def render_result_card(icon: str, color: str, title: str, content, elapsed: float = None):
    raw_text = normalize_content(content)
    word_count = len(raw_text.split())
    meta_bits = [f'<span class="meta-badge">📝 {word_count} words</span>']
    if elapsed is not None:
        meta_bits.append(f'<span class="meta-badge">⏱ {elapsed:.1f}s</span>')
    meta_html = f'<div class="meta-row">{"".join(meta_bits)}</div>'
    formatted = format_agent_text(raw_text)
    st.markdown(
        f"""
        <div class="card">
            <div class="section-title">
                <div class="chip" style="background:{color};">{icon}</div>
                {title}
            </div>
            {meta_html}
            <div class="content-box">{formatted}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Run pipeline (mirrors pipeline.py, updating the UI live between steps)
# ----------------------------------------------------------------------------
if start:
    if not topic or not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.state = {}
        st.session_state.running = True

steps_placeholder = st.empty()
results_placeholder = st.container()

if st.session_state.running:
    state = st.session_state.state
    try:
        pipeline_start = time.time()

        # ---- Step 1: Search ----
        with steps_placeholder.container():
            render_steps(1)
        t0 = time.time()
        with st.spinner("Searching the web..."):
            search_agent = build_search_agent()
            search_result = search_agent.invoke(
                {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
            )
            state["search_results"] = normalize_content(search_result["messages"][-1].content)
        with results_placeholder:
            render_result_card(
                "🔎", "linear-gradient(135deg,#1a73e8,#4285f4)", "Search Results",
                state["search_results"], elapsed=time.time() - t0,
            )

        # ---- Step 2: Read ----
        with steps_placeholder.container():
            render_steps(2)
        t0 = time.time()
        with st.spinner("Reading and scraping the best source..."):
            reader_agent = build_reader_agent()
            reader_result = reader_agent.invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"Based on the following search results about '{topic}', "
                            f"pick the most relevant URL and scrape it for deeper content.\n\n"
                            f"Search Results:\n{state['search_results'][:2000]}",
                        )
                    ]
                }
            )
            state["scraped_content"] = normalize_content(reader_result["messages"][-1].content)
        with results_placeholder:
            render_result_card(
                "📄", "linear-gradient(135deg,#34a853,#66bb6a)", "Scraped Content",
                state["scraped_content"], elapsed=time.time() - t0,
            )

        # ---- Step 3: Write ----
        with steps_placeholder.container():
            render_steps(3)
        t0 = time.time()
        with st.spinner("Writing the report..."):
            research_combined = (
                f"SEARCH RESULTS : \n {state['search_results']} \n\n"
                f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
            )
            state["report"] = normalize_content(
                writer_chain.invoke({"topic": topic, "research": research_combined})
            )
        with results_placeholder:
            render_result_card(
                "✍️", "linear-gradient(135deg,#fbbc04,#f9a825)", "Draft Report",
                state["report"], elapsed=time.time() - t0,
            )

        # ---- Step 4: Critique ----
        with steps_placeholder.container():
            render_steps(4)
        t0 = time.time()
        with st.spinner("Critiquing the report..."):
            state["feedback"] = normalize_content(critic_chain.invoke({"report": state["report"]}))
        with results_placeholder:
            render_result_card(
                "🧐", "linear-gradient(135deg,#ea4335,#ff7043)", "Critic Feedback",
                state["feedback"], elapsed=time.time() - t0,
            )

        with steps_placeholder.container():
            render_steps(5)

        total_elapsed = time.time() - pipeline_start
        st.markdown(
            f'<div style="text-align:center; position:relative; z-index:1; '
            f'color:#5f6368; font-size:0.85rem; margin-bottom:0.8rem;">'
            f'✅ Full pipeline completed in {total_elapsed:.1f}s</div>',
            unsafe_allow_html=True,
        )

        st.session_state.running = False
        st.session_state.state = state

        st.download_button(
            "⬇️  Download report as .txt",
            data=normalize_content(state.get("report", "")),
            file_name="research_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.balloons()

    except Exception as e:
        st.session_state.running = False
        st.error(f"Something went wrong while running the pipeline: {e}")
        with st.expander("Show error details"):
            st.code(traceback.format_exc())

elif st.session_state.state:
    # show last results if the app reran without a new click
    render_steps(5)
    state = st.session_state.state
    if state.get("search_results"):
        render_result_card("🔎", "linear-gradient(135deg,#1a73e8,#4285f4)", "Search Results", state["search_results"])
    if state.get("scraped_content"):
        render_result_card("📄", "linear-gradient(135deg,#34a853,#66bb6a)", "Scraped Content", state["scraped_content"])
    if state.get("report"):
        render_result_card("✍️", "linear-gradient(135deg,#fbbc04,#f9a825)", "Draft Report", state["report"])
    if state.get("feedback"):
        render_result_card("🧐", "linear-gradient(135deg,#ea4335,#ff7043)", "Critic Feedback", state["feedback"])
else:
    render_steps(0)

st.markdown(
    '<div class="footer-note">Research Agent Studio · powered by your multi-agent pipeline</div>',
    unsafe_allow_html=True,
)