import csv, json, re, argparse
from pathlib import Path

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input",  default=r"data\books.csv", help="CSV de intrare (calea)")
    ap.add_argument("--output", default="book_summaries.json", help="JSON de ieșire")
    ap.add_argument("--max",    type=int, default=2000, help="Număr maxim de cărți (0=toate)")
    ap.add_argument("--min_desc_len", type=int, default=40, help="Ignoră descrieri prea scurte")
    args = ap.parse_args()

    input_csv  = Path(args.input)
    output_json = Path(args.output)
    max_items  = args.max

    if not input_csv.exists():
        raise SystemExit(f"Nu găsesc fișierul CSV: {input_csv}")

    books = []
    seen_titles = set()

    with input_csv.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        r = csv.DictReader(f)
        # verificăm că există coloanele necesare
        req = {"title","description"}
        if not req.issubset(set(r.fieldnames or [])):
            raise SystemExit(f"Lipsesc coloane: {req - set(r.fieldnames or [])}")

        for row in r:
            title      = clean_text(row.get("title",""))
            subtitle   = clean_text(row.get("subtitle",""))
            desc       = clean_text(row.get("description",""))
            authors    = clean_text(row.get("authors",""))
            categories = clean_text(row.get("categories",""))
            year       = clean_text(row.get("published_year",""))

            if not title or len(desc) < args.min_desc_len:
                continue

            # titlu complet (dacă există subtitle)
            full_title = f"{title}: {subtitle}" if subtitle else title

            # dedup pe titlu case-insensitive
            key = full_title.lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)

            # themes: împărțim authors și categories în tokenuri
            themes = []
            if authors:
                # separăm după virgule / & / and
                parts = re.split(r"\s*(?:,|&| and )\s*", authors, flags=re.I)
                themes += [p for p in parts if p]
            if categories:
                parts = re.split(r"\s*,\s*", categories)
                themes += [p for p in parts if p]
            if year:
                themes.append(f"year:{year}")

            # optional: poți scurta descrieri foarte lungi
            # desc = desc[:2000]

            books.append({
                "title": full_title,
                "summary": desc,
                "themes": themes
            })

            if max_items and len(books) >= max_items:
                break

    with output_json.open("w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"Scris {len(books)} cărți -> {output_json.resolve()}")

if __name__ == "__main__":
    main()
