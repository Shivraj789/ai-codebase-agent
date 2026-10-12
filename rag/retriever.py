
from rag.vectorstore import create_vectorstore


def create_retriever(repo_url: str):
    """Create a retriever for the given repository."""

    vectorstore = create_vectorstore(repo_url)

    return vectorstore.as_retriever(
        search_kwargs={"k": 4}
    )


def debug_retrieval(repo_url: str, question: str):
    """Inspect the code chunks retrieved for a question."""

    vectorstore = create_vectorstore(repo_url)

    results = vectorstore.similarity_search_with_score(
        question,
        k=4,
    )

    print(f"\nQuestion: {question}")
    print(f"Retrieved chunks: {len(results)}")

    for index, (document, score) in enumerate(results, start=1):
        print("\n" + "=" * 60)
        print(f"Chunk: {index}")
        print(f"File: {document.metadata.get('file', 'Unknown')}")
        print(f"Type: {document.metadata.get('type', 'Unknown')}")
        print(f"Name: {document.metadata.get('name', 'Unknown')}")
        print(f"Score: {score}")
        print("\nCode:")
        print(document.page_content[:1000])
