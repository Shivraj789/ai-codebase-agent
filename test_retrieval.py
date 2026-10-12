
from rag.retriever import debug_retrieval

repo_url = (
    "https://github.com/dharmeshsharma8085/"
    "chatbot-deploy"
)

question = (
    "Where is the OpenAI API key configured, "
    "and how is it loaded?"
)

debug_retrieval(repo_url, question)
