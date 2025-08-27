import os, sys, json, textwrap
from typing import List, Dict, Any
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from tools import get_summary_by_title, is_clean,check_profanity

PERSIST_DIR = "chroma_db"
COLLECTION = "books"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"  # poți folosi și 'gpt-4o' sau 'gpt-4.1-mini'

SYSTEM = """Ești Smart Librarian, un asistent pentru recomandări de carte cu RAG.
Comportament:
- Dacă utilizatorul cere o recomandare (folosește cuvinte precum 'recomand', 'carte despre', 'ce să citesc', 'pentru cineva căruia îi place ...'), oferă 1 (maxim 2) titluri potrivite și explică pe scurt de ce.
- Dacă întreabă despre un TITLU anume (ex. 'Ce este 1984?'), răspunde concis cu 1 titlu și folosește rezumatul complet.
- Dacă NU cere recomandări (ex. small talk / întrebări generale), răspunde scurt și prietenos fără a recomanda cărți.
- Când oferi o recomandare, apelează tool-ul get_summary_by_title(title) pentru titlul principal.
- Răspunde conversațional, în limba română, 5–7 rânduri maxim.
"""

def build_rag_context(q: str, k: int = 5) -> str:
    chroma = chromadb.PersistentClient(path=PERSIST_DIR, settings=Settings())
    col = chroma.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    client = OpenAI()
    emb = client.embeddings.create(model=EMBED_MODEL, input=[q]).data[0].embedding
    res = col.query(query_embeddings=[emb], n_results=k, include=["documents", "metadatas"])
    lines = []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        lines.append(f"- Title: {meta['title']} | Themes: {meta.get('themes','')} | Summary: {doc}")
    return "\n".join(lines)

def tool_schema() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returnează rezumatul complet pentru un titlu exact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titlul exact al cărții."}
                    },
                    "required": ["title"]
                }
            }
        }
    ]

def call_llm(user_q: str, top_k: int = 5, temperature: float = 0.4) -> str:
    if not is_clean(user_q):
        return "Prefer să păstrez conversația prietenoasă. Te rog reformulează fără limbaj ofensator."
    
    warning = check_profanity(user_q)
    if warning:
        return warning
    
    context = build_rag_context(user_q, k=top_k)
    prompt = (
        f"Întrebare utilizator: {user_q}\n\n"
        f"Context (top {top_k} din RAG):\n{context}\n\n"
        "Instrucțiune: Decide dacă e nevoie de recomandare. Dacă recomanzi, oferă 1 (max 2) titluri și apoi apelează tool-ul pentru titlul principal. "
        "Dacă nu e despre cărți, răspunde scurt și prietenos fără tool."
    )

    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=tool_schema(),
        tool_choice="auto",
        temperature=temperature,
    )
    msg = resp.choices[0].message

    # --- Tool call handling corect ---
    if msg.tool_calls:
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            if tc.function.name == "get_summary_by_title":
                args = json.loads(tc.function.arguments)
                title = args.get("title", "")
                try:
                    summary = get_summary_by_title(title)
                except KeyError:
                    summary = f"(Nu am găsit un rezumat local pentru titlul: {title})"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": summary
                })

        final = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return final.choices[0].message.content

    return msg.content

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Setează OPENAI_API_KEY în variabilele de mediu.", file=sys.stderr)
        sys.exit(1)
    print("Smart Librarian (CLI). Scrie o întrebare (ex: 'Vreau o carte despre prietenie și magie'). 'exit' pentru ieșire.")
    while True:
        q = input("\nTu: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit", "q"}:
            break
        try:
            ans = call_llm(q)
            print("\nLibrarian:", ans)
        except Exception as e:
            print(f"Eroare: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
