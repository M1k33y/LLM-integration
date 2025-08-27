import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "book_summaries.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    _BOOKS = {b["title"]: b for b in json.load(f)}

def get_summary_by_title(title: str) -> str:
    """
    Returnează rezumatul complet (liniile lipite) pentru titlul exact.
    Ridică KeyError dacă nu există.
    """
    data = _BOOKS.get(title)
    if not data:
        raise KeyError(f"Titlul nu a fost găsit: {title}")
    return " ".join(data["summary"])

# --- Filtru simplu pentru limbaj nepotrivit (local) ---
_BAD_WORDS = {
    "naiba", "dracu", "prost", "idiot", "tâmpit", "prostie", "porcărie",
}

def is_clean(text: str) -> bool:
    text_low = text.lower()
    return not any(w in text_low for w in _BAD_WORDS)

def list_titles():
    return list(_BOOKS.keys())

_BAD_WORDS = {"prost", "idiot", "tampit", "porcarie", "bou", "taran"}

def check_profanity(text: str) -> str | None:
    text_low = text.lower()
    for w in _BAD_WORDS:
        if w in text_low:
            return f"Am observat un cuvânt jignitor („{w}”). Te rog să păstrăm conversația prietenoasă. 😊"
    return None