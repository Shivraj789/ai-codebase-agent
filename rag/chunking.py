
import os

from langchain_core.documents import Document

from rag.extraction import extract_code_structure
from rag.loader import load_repository


def create_chunks(repo_url: str):
    """Create code-aware chunks from Python files."""

    documents = load_repository(repo_url)

    repo_name = (
        repo_url.strip()
        .rstrip("/")
        .split("/")[-1]
        .replace(".git", "")
    )

    chunks = []

    repo_marker = os.path.join(
        "data",
        "repositories",
        repo_name,
    )

    for document in documents:
        source = document.metadata.get("source", "")

        if source.startswith(repo_marker):
            relative_path = os.path.relpath(
                source,
                repo_marker,
            )
        else:
            relative_path = source

        code = document.page_content

        structure = extract_code_structure(source)
        file_chunks = []

        # Function chunks
        for function in structure["functions"]:
            file_chunks.append(
                Document(
                    page_content=function["code"],
                    metadata={
                        "repository": repo_name,
                        "file": relative_path,
                        "language": "python",
                        "type": "function",
                        "name": function["name"],
                        "start_line": function["start_line"],
                        "end_line": function["end_line"],
                    },
                )
            )

        # Class chunks
        for class_info in structure["classes"]:
            file_chunks.append(
                Document(
                    page_content=class_info["code"],
                    metadata={
                        "repository": repo_name,
                        "file": relative_path,
                        "language": "python",
                        "type": "class",
                        "name": class_info["name"],
                        "start_line": class_info["start_line"],
                        "end_line": class_info["end_line"],
                    },
                )
            )

        # Fallback for files without functions or classes
        if not file_chunks and code.strip():
            file_chunks.append(
                Document(
                    page_content=code,
                    metadata={
                        "repository": repo_name,
                        "file": relative_path,
                        "language": "python",
                        "type": "module",
                        "name": os.path.basename(relative_path),
                        "start_line": 1,
                        "end_line": len(code.splitlines()),
                    },
                )
            )

        chunks.extend(file_chunks)

    if not chunks:
        raise ValueError(
            "No code chunks were created. "
            "Check whether the repository contains readable Python code."
        )

    return chunks
