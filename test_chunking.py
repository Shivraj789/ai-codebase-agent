
from rag.chunking import create_chunks

repo_url = "https://github.com/dharmeshsharma8085/chatbot-deploy"

chunks = create_chunks(repo_url)

print("Total chunks:", len(chunks))

for chunk in chunks[:5]:
    print("\n--------------------------")
    print("File:", chunk.metadata.get("file"))
    print("Type:", chunk.metadata.get("type"))
    print("Name:", chunk.metadata.get("name"))
    print(
        "Lines:",
        chunk.metadata.get("start_line"),
        "-",
        chunk.metadata.get("end_line"),
    )
    print("Code:\n", chunk.page_content[:300])
