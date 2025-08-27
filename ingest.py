import json, os
from pathlib import Path
from uuid import uuid4
import chromadb
from chromadb.config import Settings
from openai import OpenAI

DATA_PATH = Path(__file__).parent / "book_summaries.json"
PERSIST_DIR = Path(__file__).parent / "chroma_db"
EMBED_MODEL = "text-embedding-3-small"

def main():
    client = OpenAI()   # aici îl creezi o dată
    chroma = chromadb.PersistentClient(path=str(PERSIST_DIR), settings=Settings(allow_reset=True))
    collection = chroma.get_or_create_collection(name="books", metadata={"hnsw:space": "cosine"})

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    try:
        collection.delete(where={})
    except Exception:
        pass

    ids, docs, metadatas = [], [], []
    for b in books:
        ids.append(str(uuid4()))
        docs.append(" ".join(b["summary"]))
        metadatas.append({"title": b["title"], "themes": ",".join(b.get("themes", []))})

    # Embed cu OpenAI
    embeds = []
    for i in range(0, len(docs), 64):
        chunk = docs[i:i+64]
        resp = client.embeddings.create(model=EMBED_MODEL, input=chunk)
        embeds.extend([d.embedding for d in resp.data])

    collection.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeds)
    print(f"Ingested {len(ids)} cărți în colecția 'books'.")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Setează variabila de mediu OPENAI_API_KEY înainte de rulare.")
    main()
