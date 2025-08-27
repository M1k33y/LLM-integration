# 📚 Smart Librarian – AI Chatbot with RAG + OpenAI

**Smart Librarian** is an AI-powered chatbot that recommends books based on user interests.  
It combines **RAG (Retrieval-Augmented Generation)** with **ChromaDB** for semantic search across 2000+ book summaries, and **OpenAI GPT** for natural, conversational answers.

✨ Features:
- Conversational book recommendations
- **RAG** semantic search over book summaries
- **TTS (Text-to-Speech)** and **STT (Speech-to-Text)** support
- Conversation history with **export** option
- Manage **Favorites** and **To-Read** lists
- Light/Dark theme UI inspired by ChatGPT

## 🚀 Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/M1k33y/LLM-integration.git
cd LLM-integration

# 2. Create virtual environment & install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Prepare dataset (optional: adjust max number of books)
python prepare_dataset.py --input data/books.csv --output book_summaries.json --max 2000

# 4. Ingest into ChromaDB
python ingest.py

# 5. Run the app (choose one)
streamlit run streamlit_app.py
# or
python app.py
```
## 🛠️ Tech Stack
- **Python** (Flask / Streamlit)
- **ChromaDB** (vector store for RAG)
- **OpenAI GPT** (chat & embeddings)
- **TailwindCSS** (for UI)

---

## 💡 Example prompt
> *“Recommend me a book about friendship and magic.”*  
👉 The bot retrieves the most relevant summaries and gives a conversational recommendation.

---

