import html
import os
import re
from urllib.parse import urlparse

import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SyntaxIQ | Codebase Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

OVERVIEW_PROMPT = """
Analyze this repository using the available code context.
Explain its purpose, entry point, important files, functions,
classes, technologies, dependencies, and execution flow.
Mention relevant file paths. Do not invent repository details.
State clearly when the retrieved context is insufficient.
"""

ARCHITECTURE_PROMPT = """
Explain this repository's architecture using available code.
Describe the main components, their responsibilities,
relationships, dependencies, and execution flow.
Mention relevant file paths. Do not invent components.
"""

KEY_FILES_PROMPT = """
Identify important files in this repository using available
code context. Explain their responsibilities and relationships.
Mention file paths and do not invent repository details.
"""

DEPENDENCIES_PROMPT = """
Explain the dependencies and external services used in this
repository based on available code. Mention where they are
imported or configured. Do not invent dependencies.
"""

TECHNOLOGIES_PROMPT = (
    "Identify the technologies and frameworks used in this "
    "repository from available code evidence. Mention files "
    "and state uncertainty where evidence is insufficient."
)

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "conversations": {"chat-1": {"title": "New Chat", "messages": []}},
    "active_chat_id": "chat-1",
    "next_chat_number": 2,
    "repo_url_input": "",
    "loaded_repo": "",
    "pending_prompt": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def current_chat():
    return st.session_state.conversations[st.session_state.active_chat_id]


# =========================================================
# THEME — iOS LIQUID GLASS
# =========================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --ios-blue: #0a84ff;
        --ios-blue-2: #409cff;
        --ios-text: rgba(255,255,255,0.96);
        --ios-muted: rgba(235,235,245,0.62);
        --glass: rgba(255,255,255,0.07);
        --glass-strong: rgba(255,255,255,0.12);
        --glass-border: rgba(255,255,255,0.16);
        --glass-shadow: 0 8px 32px rgba(0,0,0,0.45),
                        inset 0 1px 0 rgba(255,255,255,0.22),
                        inset 0 -1px 0 rgba(255,255,255,0.04);
    }

    html, body, .stApp, [class*="st-"], button, input, textarea {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                     "SF Pro Text", "Inter", "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    .stApp {
        background:
            radial-gradient(1200px 700px at 12% -10%, #14123a 0%, transparent 60%),
            radial-gradient(900px 600px at 110% 10%, #0b2447 0%, transparent 55%),
            #000 !important;
        color: var(--ios-text) !important;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: transparent !important;
        position: relative;
        z-index: 1;
    }

    [data-testid="stHeader"] {
        background: rgba(0,0,0,0.25) !important;
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stHeader"] * { color: var(--ios-text) !important; }

    .block-container {
        max-width: 1700px;
        padding-top: 1.25rem;
        padding-bottom: 2rem;
    }

    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp label, .stApp li, .stApp span {
        color: var(--ios-text);
        letter-spacing: -0.01em;
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p { color: var(--ios-muted) !important; }

    /* Sidebar = floating glass sheet */
    [data-testid="stSidebar"] {
        background: rgba(20,20,24,0.55) !important;
        backdrop-filter: blur(40px) saturate(180%);
        -webkit-backdrop-filter: blur(40px) saturate(180%);
        border-right: 1px solid var(--glass-border);
    }
    [data-testid="stSidebar"] > div:first-child { background: transparent !important; }

    .muted { color: var(--ios-muted) !important; font-size: .84rem; line-height: 1.6; }

    .section-label {
        color: var(--ios-muted) !important;
        font-size: .72rem; font-weight: 600;
        letter-spacing: .08em; text-transform: uppercase;
        margin: 1.1rem 0 .5rem .25rem;
    }

    /* Glass cards */
    .glass-card {
        background: var(--glass);
        border: 1px solid var(--glass-border);
        border-radius: 28px;
        padding: 1.2rem 1.3rem;
        margin: .4rem 0 .9rem;
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        box-shadow: var(--glass-shadow);
    }

    .hero-title {
        font-size: 2.4rem; font-weight: 700;
        letter-spacing: -0.04em; line-height: 1.1;
        background: linear-gradient(180deg,#fff 0%,rgba(255,255,255,.65) 100%);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tagline { color: var(--ios-blue-2) !important; font-weight: 600; font-size: 1rem; }
    .repo-heading { font-size: .85rem; font-weight: 600; color: var(--ios-muted) !important; margin: 0 0 .4rem .3rem; }
    .repo-name { font-size: 1.1rem; font-weight: 650; overflow-wrap: anywhere; }
    .repo-url  { color: var(--ios-muted) !important; font-size: .82rem; overflow-wrap: anywhere; }

    .tech-tag {
        display: inline-block;
        background: rgba(10,132,255,.16);
        color: #8ec5ff !important;
        border: 1px solid rgba(10,132,255,.35);
        border-radius: 999px;
        padding: .28rem .7rem; margin: .15rem .15rem .15rem 0;
        font-size: .75rem; font-weight: 550;
    }

    /* Inputs */
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,.08) !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
        caret-color: var(--ios-blue-2) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        min-height: 2.9rem;
        backdrop-filter: blur(20px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.1);
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: rgba(235,235,245,.45) !important;
        -webkit-text-fill-color: rgba(235,235,245,.45) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--ios-blue) !important;
        box-shadow: 0 0 0 3px rgba(10,132,255,.35) !important;
    }

    /* Buttons */
    div[data-testid="stButton"] > button,
    div[data-testid="stLinkButton"] > a {
        background: var(--glass-strong) !important;
        color: var(--ios-text) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        min-height: 2.6rem; font-weight: 550;
        backdrop-filter: blur(20px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
        transition: transform .18s cubic-bezier(.2,.8,.2,1), background .18s;
    }
    div[data-testid="stButton"] > button p,
    div[data-testid="stLinkButton"] > a p { color: var(--ios-text) !important; }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stLinkButton"] > a:hover {
        background: rgba(255,255,255,.2) !important;
        border-color: rgba(255,255,255,.3) !important;
        transform: scale(1.015);
    }
    div[data-testid="stButton"] > button:active { transform: scale(.97); }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(180deg, #3d9bff 0%, #0a84ff 100%) !important;
        border: 1px solid rgba(255,255,255,.28) !important;
        box-shadow: 0 6px 20px rgba(10,132,255,.45),
                    inset 0 1px 0 rgba(255,255,255,.4);
    }
    div[data-testid="stButton"] > button[kind="primary"] p { color: #fff !important; }

    /* Tabs = iOS segmented control */
    div[data-testid="stTabs"] [role="tablist"] {
        background: rgba(255,255,255,.07);
        border: 1px solid var(--glass-border);
        border-radius: 999px; padding: 4px; gap: 2px;
        backdrop-filter: blur(24px);
        overflow-x: auto;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        border-radius: 999px !important;
        background: transparent !important;
        height: 2.2rem; padding: 0 1rem;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p {
        color: var(--ios-muted) !important; font-weight: 550; font-size: .88rem;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(255,255,255,.2) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.3);
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p { color: #fff !important; }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 24px !important;
        padding: .9rem 1rem !important;
        margin-bottom: .75rem;
        backdrop-filter: blur(24px) saturate(160%);
        -webkit-backdrop-filter: blur(24px) saturate(160%);
        box-shadow: var(--glass-shadow);
    }
    [data-testid="stChatInput"] {
        background: rgba(255,255,255,.1) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 999px !important;
        backdrop-filter: blur(30px);
        box-shadow: var(--glass-shadow);
    }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #fff !important;
        -webkit-text-fill-color: #fff !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: rgba(235,235,245,.45) !important;
        -webkit-text-fill-color: rgba(235,235,245,.45) !important;
    }
    [data-testid="stBottom"] > div { background: transparent !important; }

    [data-testid="stCode"], [data-testid="stExpander"] {
        border-color: var(--glass-border) !important;
        border-radius: 18px !important;
    }
    [data-testid="stExpander"] { background: var(--glass); backdrop-filter: blur(20px); }
    details summary, details summary p { color: var(--ios-text) !important; }

    [data-testid="stAlert"] {
        border-radius: 20px; backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
    }

    hr { border-color: rgba(255,255,255,.1) !important; }

    .footer {
        color: var(--ios-muted) !important; font-size: .8rem; text-align: center;
        border-top: 1px solid rgba(255,255,255,.1);
        padding-top: 1.2rem; margin-top: 2.5rem;
    }
    .footer strong { color: var(--ios-text) !important; }
    a { color: var(--ios-blue-2) !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.2); border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# TAILWIND (CDN) + GSAP (CDN) — injected into the parent page
# GSAP animates 3 floating background orbs + glass card entrance
# =========================================================

components.html(
    """
    <script>
    (function () {
      const p = window.parent;
      const d = p.document;

      function addScript(src, id, onload) {
        if (d.getElementById(id)) { onload && onload(); return; }
        const s = d.createElement("script");
        s.id = id; s.src = src; s.onload = onload;
        d.head.appendChild(s);
      }

      // Tailwind CDN: disable preflight so Streamlit's own base styles stay intact
      if (!p.tailwind) {
        p.tailwind = { config: { corePlugins: { preflight: false } } };
      }
      addScript("https://cdn.tailwindcss.com", "siq-tailwind");

      function buildOrbs() {
        const orbs = [
          { id: "siq-orb-1", size: 520, color: "#0a84ff", top: "-8%",  left: "-6%"  },
          { id: "siq-orb-2", size: 460, color: "#bf5af2", top: "35%",  left: "70%"  },
          { id: "siq-orb-3", size: 420, color: "#30d5c8", top: "75%",  left: "20%"  },
        ];
        orbs.forEach(o => {
          if (d.getElementById(o.id)) return;
          const el = d.createElement("div");
          el.id = o.id;
          el.className = "siq-orb fixed rounded-full blur-3xl opacity-40 pointer-events-none";
          el.style.cssText =
            "position:fixed;z-index:0;pointer-events:none;border-radius:9999px;" +
            "filter:blur(90px);opacity:.38;" +
            `width:${o.size}px;height:${o.size}px;background:${o.color};` +
            `top:${o.top};left:${o.left};`;
          d.body.appendChild(el);
        });
      }

      function animate() {
        const gsap = p.gsap;
        buildOrbs();

        // 3 floating orbs (set up once)
        if (!p.__siqOrbsAnimated) {
          p.__siqOrbsAnimated = true;
          [["#siq-orb-1", 140, 90, 14], ["#siq-orb-2", -160, 110, 17], ["#siq-orb-3", 120, -100, 20]]
            .forEach(([sel, x, y, dur]) => {
              gsap.to(d.querySelector(sel), {
                x, y, scale: 1.18, duration: dur,
                ease: "sine.inOut", repeat: -1, yoyo: true,
              });
            });
        }

        // Entrance for new glass elements only
        const targets = Array.from(
          d.querySelectorAll(".glass-card, .hero-title, [data-testid='stChatMessage']")
        ).filter(el => !el.dataset.siq);

        targets.forEach(el => (el.dataset.siq = "1"));
        if (targets.length) {
          gsap.from(targets, {
            y: 28, opacity: 0, scale: 0.97,
            duration: 0.8, stagger: 0.09, ease: "power3.out",
          });
        }
      }

      function boot() {
        if (p.gsap) { animate(); return; }
        addScript(
          "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js",
          "siq-gsap",
          animate
        );
      }
      boot();
    })();
    </script>
    """,
    height=0,
)

# =========================================================
# BACKEND HELPERS
# =========================================================


def ask_backend(repo_url: str, question: str) -> str:
    """Send a question to the existing FastAPI endpoint."""
    response = requests.post(
        f"{BACKEND_URL.rstrip('/')}/api/ask",
        json={"repo_url": repo_url.strip(), "question": question.strip()},
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    answer = data.get("response")

    if not answer:
        raise ValueError("The backend returned an empty response.")

    return str(answer)


def extract_file_references(answer: str) -> list[str]:
    """Extract likely file paths mentioned in the response."""
    pattern = re.compile(
        r"(?<![\w.-])"
        r"(?:[\w.-]+[\\/])*[\w.-]+\."
        r"(?:py|js|jsx|ts|tsx|java|cpp|c|h|go|rs|"
        r"json|yaml|yml|toml|md|html|css|sql|txt)"
        r"(?![\w.-])",
        re.IGNORECASE,
    )
    return list(dict.fromkeys(pattern.findall(answer)))


def parse_repo_url(url: str) -> dict:
    """Extract owner and repository name from a GitHub URL."""
    parsed = urlparse(url.strip())
    parts = [part for part in parsed.path.split("/") if part]

    if parsed.hostname not in {"github.com", "www.github.com"}:
        return {"owner": "", "name": "", "url": url.strip()}

    owner = parts[0] if len(parts) >= 1 else ""
    name = parts[1].removesuffix(".git") if len(parts) >= 2 else ""

    return {"owner": owner, "name": name, "url": url.strip()}


def new_chat():
    number = st.session_state.next_chat_number
    chat_id = f"chat-{number}"

    st.session_state.next_chat_number = number + 1
    st.session_state.conversations[chat_id] = {"title": "New Chat", "messages": []}
    st.session_state.active_chat_id = chat_id


def render_message(message: dict):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            refs = extract_file_references(message["content"])

            if refs:
                with st.expander(f"Referenced files · {len(refs)}"):
                    for path in refs:
                        st.code(path, language=None)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        '<div class="text-3xl font-bold tracking-tight text-white">'
        '🧠 Syntax<span style="color:#409cff">IQ</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted">Understand Any Repo. Any Language. Any Syntax.</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("＋  New Chat", type="primary", use_container_width=True):
        new_chat()
        st.rerun()

    search_query = st.text_input(
        "Search conversations",
        placeholder="🔍  Search conversations",
        label_visibility="collapsed",
        key="conversation_search",
    )

    st.markdown('<div class="section-label">Workspace</div>', unsafe_allow_html=True)

    workspace_actions = {
        "▣  Project Overview": OVERVIEW_PROMPT,
        "⌘  Architecture Analysis": ARCHITECTURE_PROMPT,
        "⌕  Find & Explain Code": (
            "Explain the relevant code for my question. "
            "Identify files, functions, and data flow."
        ),
        "⚒  Debug & Fix Issues": (
            "Help investigate the root cause of a bug using "
            "available code context. Mention affected files "
            "and propose a safe fix."
        ),
        "⇄  Dependencies & Setup": DEPENDENCIES_PROMPT,
        "▤  Generate Documentation": (
            "Explain how to document this repository based on "
            "verified code context. Cover setup, usage, and modules."
        ),
    }

    for label, prompt_text in workspace_actions.items():
        if st.button(label, use_container_width=True):
            st.session_state.pending_prompt = prompt_text
            st.rerun()

    st.markdown('<div class="section-label">Recent Chats</div>', unsafe_allow_html=True)

    for chat_id, chat in reversed(list(st.session_state.conversations.items())):
        title = chat["title"]

        if search_query and search_query.lower() not in title.lower():
            continue

        prefix = "●" if chat_id == st.session_state.active_chat_id else "○"

        if st.button(f"{prefix}  {title}", key=f"select_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

    st.divider()

    st.markdown("**SyntaxIQ**")
    st.caption("AI-powered codebase intelligence")
    st.caption("FastAPI · LangGraph · RAG")
    st.markdown(
        '<div class="muted">Developed by <strong>Dharmesh Sharma</strong></div>',
        unsafe_allow_html=True,
    )

# =========================================================
# TOP REPOSITORY BAR
# =========================================================

repo_input_col, load_col = st.columns([5, 1.35], gap="small")

with repo_input_col:
    st.markdown('<div class="repo-heading">GitHub Repository</div>', unsafe_allow_html=True)
    st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository",
        key="repo_url_input",
        label_visibility="collapsed",
    )

with load_col:
    st.markdown('<div class="repo-heading">&nbsp;</div>', unsafe_allow_html=True)
    load_clicked = st.button("Load Repository →", type="primary", use_container_width=True)

repo_url = st.session_state.repo_url_input.strip()

st.markdown(
    '<div style="border-bottom:1px solid rgba(255,255,255,.1);margin:.7rem 0 1.2rem;"></div>',
    unsafe_allow_html=True,
)

if load_clicked:
    details = parse_repo_url(repo_url)

    if not details["owner"] or not details["name"]:
        st.error(
            "Enter a valid GitHub repository URL, for example "
            "https://github.com/owner/repository"
        )
    else:
        st.session_state.loaded_repo = repo_url
        st.session_state.pending_prompt = None
        st.success(
            f"Repository selected: {details['owner']}/{details['name']}. "
            "Ask a question or choose an analysis action."
        )

# =========================================================
# WORKSPACE DATA
# =========================================================

loaded_repo = st.session_state.loaded_repo
repo_details = (
    parse_repo_url(loaded_repo)
    if loaded_repo
    else {"owner": "", "name": "", "url": ""}
)

chat_col, info_col = st.columns([2.55, 1], gap="medium")

# =========================================================
# CHAT WORKSPACE
# =========================================================

with chat_col:
    st.markdown('<div class="hero-title">SyntaxIQ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tagline">Understand Any Repo. Any Language. Any Syntax.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Explore code, understand architecture, and investigate bugs.")

    tabs = st.tabs(
        ["Chat", "Overview", "Architecture", "Key Files", "Technologies", "Dependencies"]
    )

    with tabs[0]:
        if not current_chat()["messages"]:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="text-xl font-semibold tracking-tight">Welcome to SyntaxIQ</div>
                    <p class="muted" style="margin-top:.35rem">
                        Ask questions about unfamiliar code, architecture,
                        dependencies, and debugging.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            quick_left, quick_right = st.columns(2)

            with quick_left:
                if st.button("Explain this repository", use_container_width=True):
                    st.session_state.pending_prompt = OVERVIEW_PROMPT
                    st.rerun()
                if st.button("Explain architecture", use_container_width=True):
                    st.session_state.pending_prompt = ARCHITECTURE_PROMPT
                    st.rerun()

            with quick_right:
                if st.button("Explain dependencies", use_container_width=True):
                    st.session_state.pending_prompt = DEPENDENCIES_PROMPT
                    st.rerun()
                if st.button("Identify key files", use_container_width=True):
                    st.session_state.pending_prompt = KEY_FILES_PROMPT
                    st.rerun()

        for message in current_chat()["messages"]:
            render_message(message)

    with tabs[1]:
        st.markdown("### Repository Overview")
        st.caption("Ask the backend to summarize the selected repository.")
        if st.button("Analyze repository overview", key="overview_action"):
            st.session_state.pending_prompt = OVERVIEW_PROMPT
            st.rerun()

    with tabs[2]:
        st.markdown("### Architecture")
        st.caption("Explore components, relationships, and execution flow.")
        if st.button("Analyze architecture", key="architecture_action"):
            st.session_state.pending_prompt = ARCHITECTURE_PROMPT
            st.rerun()

    with tabs[3]:
        st.markdown("### Key Files")
        st.caption("Identify important files using the available code context.")
        if st.button("Identify key files", key="keyfiles_action"):
            st.session_state.pending_prompt = KEY_FILES_PROMPT
            st.rerun()

    with tabs[4]:
        st.markdown("### Technologies")
        st.caption("Ask the backend to identify technologies from code evidence.")
        if st.button("Analyze technologies", key="technologies_action"):
            st.session_state.pending_prompt = TECHNOLOGIES_PROMPT
            st.rerun()

    with tabs[5]:
        st.markdown("### Dependencies")
        st.caption("Inspect imports, dependency declarations, and external services.")
        if st.button("Analyze dependencies", key="dependencies_action"):
            st.session_state.pending_prompt = DEPENDENCIES_PROMPT
            st.rerun()

    chat_prompt = st.chat_input("Ask SyntaxIQ about your codebase...")

# =========================================================
# REPOSITORY INFORMATION PANEL
# =========================================================

with info_col:
    st.markdown("### Repository Information")

    if loaded_repo:
        safe_name = html.escape(repo_details["name"])
        safe_owner = html.escape(repo_details["owner"])
        safe_url = html.escape(repo_details["url"], quote=True)

        st.markdown(
            f"""
            <div class="glass-card">
                <div class="repo-name">◉ &nbsp; {safe_name}</div>
                <div class="muted">{safe_owner}</div>
                <br>
                <div class="repo-url">{safe_url}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.link_button("Open repository ↗", loaded_repo, use_container_width=True)
    else:
        st.info("Enter a GitHub URL and click Load Repository.")

    st.divider()

    st.markdown("### Codebase Context")
    st.markdown(
        """
        <div class="muted">
            Answers use your existing FastAPI, LangGraph, and RAG pipeline.
            Verified file tree and GitHub statistics are not yet exposed
            by the current backend.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Current Stack")

    for item in ["Streamlit UI", "FastAPI", "LangGraph", "RAG", "ChromaDB"]:
        st.markdown(f'<span class="tech-tag">{item}</span>', unsafe_allow_html=True)

    st.divider()

    if st.button("Refresh repository overview", use_container_width=True):
        st.session_state.pending_prompt = OVERVIEW_PROMPT
        st.rerun()

# =========================================================
# PROCESS CHAT AND QUICK ACTIONS
# =========================================================

prompt = st.session_state.pending_prompt or chat_prompt
st.session_state.pending_prompt = None

if prompt:
    if not loaded_repo:
        st.warning(
            "First enter a valid GitHub repository URL and click Load Repository."
        )
    else:
        chat = current_chat()
        chat["messages"].append({"role": "user", "content": prompt})

        if chat["title"] == "New Chat":
            chat["title"] = prompt.strip()[:34]

        try:
            with st.spinner("SyntaxIQ is analyzing the repository..."):
                answer = ask_backend(loaded_repo, prompt)

            chat["messages"].append({"role": "assistant", "content": answer})
            st.rerun()

        except requests.exceptions.ConnectionError:
            chat["messages"].pop()
            st.error(
                "Cannot connect to FastAPI. Start the backend using "
                "`uv run uvicorn app.main:app --reload`."
            )

        except requests.exceptions.Timeout:
            chat["messages"].pop()
            st.error(
                "The request timed out. Check the backend terminal; "
                "repository indexing or LLM generation may take time."
            )

        except requests.exceptions.HTTPError as error:
            chat["messages"].pop()
            st.error(f"FastAPI returned an HTTP error: {error}")

        except (ValueError, requests.exceptions.RequestException) as error:
            chat["messages"].pop()
            st.error(f"Request failed: {error}")

# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        <strong>SyntaxIQ</strong><br>
        Understand Any Repo. Any Language. Any Syntax.
        <br><br>
        Developed with ❤️ by <strong>Dharmesh Sharma</strong>
        <br>
        <a href="https://github.com/dharmeshsharma8085" target="_blank">
            GitHub · @dharmeshsharma8085
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)