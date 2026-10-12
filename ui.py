
import html
import os
import re
from urllib.parse import urlparse

import requests
import streamlit as st
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

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)

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

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "conversations": {
        "chat-1": {
            "title": "New Chat",
            "messages": [],
        }
    },
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
    return st.session_state.conversations[
        st.session_state.active_chat_id
    ]


# =========================================================
# THEME — NEAR BLACK, HIGH CONTRAST
# =========================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --bg: #0a0a0a;
        --sidebar: #0d0d0d;
        --panel: #111111;
        --panel-hover: #191919;
        --border: #303030;
        --text: #f5f5f5;
        --muted: #b0b0b0;
        --accent: #3b82f6;
        --accent-hover: #60a5fa;
    }

    html, body, .stApp {
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    [data-testid="stHeader"] {
        background: #0a0a0a !important;
        border-bottom: 1px solid #202020;
    }

    [data-testid="stHeader"] *,
    [data-testid="stToolbar"] * {
        color: #f5f5f5 !important;
    }

    [data-testid="stSidebar"] {
        background: var(--sidebar) !important;
        border-right: 1px solid #292929;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: var(--sidebar) !important;
    }

    .block-container {
        max-width: 1800px;
        padding-top: 1.25rem;
        padding-bottom: 2rem;
    }

    /* General readable text */
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp p,
    .stApp label,
    .stApp li {
        color: var(--text);
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: var(--muted) !important;
    }

    /* Brand */
    .brand {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        color: #ffffff !important;
        line-height: 1.25;
    }

    .brand-accent {
        color: #818cf8 !important;
    }

    .muted {
        color: var(--muted) !important;
        font-size: 0.84rem;
        line-height: 1.6;
    }

    .section-label {
        color: #a3a3a3 !important;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 1.3px;
        text-transform: uppercase;
        margin: 1rem 0 0.55rem;
    }

    /* Repository top bar */
    .repo-heading {
        color: #f5f5f5 !important;
        font-size: 0.86rem;
        font-weight: 650;
        margin: 0 0 0.4rem 0;
    }

    div[data-testid="stTextInput"] {
        width: 100%;
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p {
        color: #e5e5e5 !important;
    }

    div[data-testid="stTextInput"] input {
        background-color: #171717 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #ffffff !important;
        border: 1px solid #454545 !important;
        border-radius: 10px !important;
        min-height: 2.8rem;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #bdbdbd !important;
        -webkit-text-fill-color: #bdbdbd !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }

    /* Buttons */
    div[data-testid="stButton"] > button,
    div[data-testid="stLinkButton"] > a {
        background-color: #171717 !important;
        color: #f5f5f5 !important;
        border: 1px solid #393939 !important;
        border-radius: 10px !important;
        min-height: 2.55rem;
        font-weight: 550;
    }

    div[data-testid="stButton"] > button p,
    div[data-testid="stLinkButton"] > a p {
        color: #f5f5f5 !important;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stLinkButton"] > a:hover {
        background-color: #222222 !important;
        border-color: #606060 !important;
    }

    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
    }

    div[data-testid="stButton"] > button[kind="primary"] p {
        color: #ffffff !important;
    }

    /* Main panels */
    .welcome-panel,
    .repo-panel {
        background: #111111;
        border: 1px solid #303030;
        border-radius: 14px;
        padding: 1.1rem;
        margin: 0.5rem 0 0.8rem;
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 1.55rem;
        font-weight: 780;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
    }

    .tagline {
        color: #93a5ff !important;
        font-weight: 650;
        font-size: 0.95rem;
    }

    .repo-name {
        color: #ffffff !important;
        font-size: 1.05rem;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .repo-url {
        color: #c4c4c4 !important;
        font-size: 0.82rem;
        overflow-wrap: anywhere;
        line-height: 1.6;
    }

    .tech-tag {
        display: inline-block;
        background: #17202e;
        color: #93c5fd !important;
        border: 1px solid #2a3a50;
        border-radius: 999px;
        padding: 0.3rem 0.6rem;
        margin: 0.15rem 0.12rem 0.15rem 0;
        font-size: 0.75rem;
    }

    /* Tabs */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        color: #c0c0c0 !important;
        background: transparent !important;
        border-bottom-color: transparent !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] p {
        color: #c0c0c0 !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #60a5fa !important;
        border-bottom-color: #3b82f6 !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {
        color: #60a5fa !important;
    }

    /* Chat */
    div[data-testid="stChatMessage"] {
        background: #101010 !important;
        border: 1px solid #292929 !important;
        border-radius: 14px !important;
        padding: 0.85rem !important;
        margin-bottom: 0.7rem;
    }

    [data-testid="stChatInput"] {
        background: #191919 !important;
        border: 1px solid #414141 !important;
        border-radius: 13px !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #191919 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #bdbdbd !important;
        -webkit-text-fill-color: #bdbdbd !important;
        opacity: 1 !important;
    }

    /* Code blocks and expanders */
    [data-testid="stCode"],
    [data-testid="stExpander"] {
        border-color: #343434 !important;
    }

    details summary,
    details summary p {
        color: #eeeeee !important;
    }

    /* Dividers and footer */
    hr {
        border-color: #2b2b2b !important;
    }

    .footer {
        color: #a0a0a0 !important;
        font-size: 0.8rem;
        text-align: center;
        border-top: 1px solid #292929;
        padding-top: 1.2rem;
        margin-top: 2.5rem;
    }

    .footer strong {
        color: #f0f0f0 !important;
    }

    a {
        color: #60a5fa !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# BACKEND HELPERS
# =========================================================

def ask_backend(repo_url: str, question: str) -> str:
    """Send a question to the existing FastAPI endpoint."""

    response = requests.post(
        f"{BACKEND_URL.rstrip('/')}/api/ask",
        json={
            "repo_url": repo_url.strip(),
            "question": question.strip(),
        },
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

    return {
        "owner": owner,
        "name": name,
        "url": url.strip(),
    }


def new_chat():
    number = st.session_state.next_chat_number
    chat_id = f"chat-{number}"

    st.session_state.next_chat_number = number + 1
    st.session_state.conversations[chat_id] = {
        "title": "New Chat",
        "messages": [],
    }
    st.session_state.active_chat_id = chat_id


def render_message(message: dict):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            refs = extract_file_references(message["content"])

            if refs:
                with st.expander(
                    f"Referenced files · {len(refs)}"
                ):
                    for path in refs:
                        st.code(path, language=None)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        '<div class="brand">🧠 Syntax<span class="brand-accent">IQ</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted">'
        'Understand Any Repo. Any Language. Any Syntax.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "＋  New Chat",
        type="primary",
        use_container_width=True,
    ):
        new_chat()
        st.rerun()

    search_query = st.text_input(
        "Search conversations",
        placeholder="Search conversations...",
        label_visibility="collapsed",
        key="conversation_search",
    )

    st.markdown(
        '<div class="section-label">Workspace</div>',
        unsafe_allow_html=True,
    )

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

    st.markdown(
        '<div class="section-label">Recent Chats</div>',
        unsafe_allow_html=True,
    )

    for chat_id, chat in reversed(
        list(st.session_state.conversations.items())
    ):
        title = chat["title"]

        if search_query and search_query.lower() not in title.lower():
            continue

        prefix = (
            "●" if chat_id == st.session_state.active_chat_id else "○"
        )

        if st.button(
            f"{prefix}  {title}",
            key=f"select_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.active_chat_id = chat_id
            st.rerun()

    st.divider()

    st.markdown("**SyntaxIQ**")
    st.caption("AI-powered codebase intelligence")
    st.caption("FastAPI · LangGraph · RAG")

    st.markdown(
        '<div class="muted">'
        'Developed by <strong>Dharmesh Sharma</strong>'
        '</div>',
        unsafe_allow_html=True,
    )

# =========================================================
# TOP REPOSITORY BAR — FIXED VISIBILITY
# =========================================================

repo_input_col, load_col = st.columns([5, 1.35], gap="small")

with repo_input_col:
    st.markdown(
        '<div class="repo-heading">GitHub Repository</div>',
        unsafe_allow_html=True,
    )

    st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository",
        key="repo_url_input",
        label_visibility="collapsed",
    )

with load_col:
    st.markdown(
        '<div class="repo-heading">&nbsp;</div>',
        unsafe_allow_html=True,
    )

    load_clicked = st.button(
        "Load Repository →",
        type="primary",
        use_container_width=True,
    )

repo_url = st.session_state.repo_url_input.strip()

st.markdown(
    """
    <div style="
        border-bottom: 1px solid #292929;
        margin: 0.7rem 0 1.2rem;
    "></div>
    """,
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
repo_details = parse_repo_url(loaded_repo) if loaded_repo else {
    "owner": "",
    "name": "",
    "url": "",
}

chat_col, info_col = st.columns(
    [2.55, 1],
    gap="medium",
)

# =========================================================
# CHAT WORKSPACE
# =========================================================

with chat_col:
    st.markdown(
        '<div class="hero-title">SyntaxIQ</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tagline">'
        'Understand Any Repo. Any Language. Any Syntax.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Explore code, understand architecture, and investigate bugs."
    )

    tabs = st.tabs(
        [
            "Chat",
            "Repository Overview",
            "Architecture",
            "Key Files",
            "Technologies",
            "Dependencies",
        ]
    )

    with tabs[0]:
        if not current_chat()["messages"]:
            st.markdown(
                """
                <div class="welcome-panel">
                    <div class="panel-title">Welcome to SyntaxIQ</div>
                    <p style="color:#b0b0b0">
                        Ask questions about unfamiliar code, architecture,
                        dependencies, and debugging.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            quick_left, quick_right = st.columns(2)

            with quick_left:
                if st.button(
                    "Explain this repository",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = OVERVIEW_PROMPT
                    st.rerun()

                if st.button(
                    "Explain architecture",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = ARCHITECTURE_PROMPT
                    st.rerun()

            with quick_right:
                if st.button(
                    "Explain dependencies",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = DEPENDENCIES_PROMPT
                    st.rerun()

                if st.button(
                    "Identify key files",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = KEY_FILES_PROMPT
                    st.rerun()

        for message in current_chat()["messages"]:
            render_message(message)

    with tabs[1]:
        st.markdown("### Repository Overview")
        st.caption(
            "Ask the backend to summarize the selected repository."
        )

        if st.button("Analyze repository overview", key="overview_action"):
            st.session_state.pending_prompt = OVERVIEW_PROMPT
            st.rerun()

    with tabs[2]:
        st.markdown("### Architecture")
        st.caption(
            "Explore components, relationships, and execution flow."
        )

        if st.button("Analyze architecture", key="architecture_action"):
            st.session_state.pending_prompt = ARCHITECTURE_PROMPT
            st.rerun()

    with tabs[3]:
        st.markdown("### Key Files")
        st.caption(
            "Identify important files using the available code context."
        )

        if st.button("Identify key files", key="keyfiles_action"):
            st.session_state.pending_prompt = KEY_FILES_PROMPT
            st.rerun()

    with tabs[4]:
        st.markdown("### Technologies")
        st.caption(
            "Ask the backend to identify technologies from code evidence."
        )

        if st.button("Analyze technologies", key="technologies_action"):
            st.session_state.pending_prompt = (
                "Identify the technologies and frameworks used in this "
                "repository from available code evidence. Mention files "
                "and state uncertainty where evidence is insufficient."
            )
            st.rerun()

    with tabs[5]:
        st.markdown("### Dependencies")
        st.caption(
            "Inspect imports, dependency declarations, and external services."
        )

        if st.button("Analyze dependencies", key="dependencies_action"):
            st.session_state.pending_prompt = DEPENDENCIES_PROMPT
            st.rerun()

    chat_prompt = st.chat_input(
        "Ask SyntaxIQ about your codebase..."
    )

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
            <div class="repo-panel">
                <div class="repo-name">◉ &nbsp; {safe_name}</div>
                <div class="muted">{safe_owner}</div>
                <br>
                <div class="repo-url">{safe_url}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.link_button(
            "Open repository ↗",
            loaded_repo,
            use_container_width=True,
        )
    else:
        st.info(
            "Enter a GitHub URL and click Load Repository."
        )

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

    for item in [
        "Streamlit UI",
        "FastAPI",
        "LangGraph",
        "RAG",
        "ChromaDB",
    ]:
        st.markdown(
            f'<span class="tech-tag">{item}</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    if st.button(
        "Refresh repository overview",
        use_container_width=True,
    ):
        st.session_state.pending_prompt = OVERVIEW_PROMPT
        st.rerun()

# =========================================================
# PROCESS CHAT AND QUICK ACTIONS
# =========================================================

prompt = (
    st.session_state.pending_prompt
    or chat_prompt
)

st.session_state.pending_prompt = None

if prompt:
    if not loaded_repo:
        st.warning(
            "First enter a valid GitHub repository URL and click "
            "Load Repository."
        )
    else:
        chat = current_chat()

        chat["messages"].append(
            {"role": "user", "content": prompt}
        )

        if chat["title"] == "New Chat":
            chat["title"] = prompt[:34]

        try:
            with st.spinner(
                "SyntaxIQ is analyzing the repository..."
            ):
                answer = ask_backend(loaded_repo, prompt)

            chat["messages"].append(
                {"role": "assistant", "content": answer}
            )

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

        except (
            ValueError,
            requests.exceptions.RequestException,
        ) as error:
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
        <a href="https://github.com/dharmeshsharma8085"
           target="_blank">
            GitHub · @dharmeshsharma8085
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
