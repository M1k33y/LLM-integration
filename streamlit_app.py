# streamlit_app.py
import os
import streamlit as st
from openai import OpenAI

from app_cli import call_llm
from tools import list_titles

# ---------- Config pagină ----------
st.set_page_config(page_title="Smart Librarian", page_icon="📚", layout="centered")
st.title("📚 Smart Librarian — RAG + Tool Completion")

# ---------- Sidebar: setări ----------
with st.sidebar:
    st.header("Setări")
    top_k = st.slider("Top-K RAG", min_value=1, max_value=10, value=5)
    temperature = st.slider("Creativitate (temperature)", 0.0, 1.2, 0.4, 0.1)
    voice_out = st.toggle("🔊 Voice output (TTS)", value=False)
    st.divider()

    if st.button("🧹 Reset chat"):
        st.session_state.chat = []
        st.rerun()

    st.caption(
        "Cheia OpenAI trebuie să fie setată ca variabilă de mediu **OPENAI_API_KEY**."
    )
    with st.expander("Titluri disponibile local"):
        st.write(", ".join(list_titles()))

if not os.environ.get("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY nu este setată în mediul curent.", icon="⚠️")

# ---------- Utilitare ----------
def say(text: str) -> bytes:
    """Generează TTS și întoarce bytes (mp3). Nu face st.audio aici!"""
    from openai import OpenAI
    client = OpenAI()

    resp = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    # în SDK 1.101.0 merge .read() pentru bytes
    return resp.read()

# ---------- Stare chat ----------
if "chat" not in st.session_state:
    st.session_state.chat = []  # list[tuple(role, content)]

# ---------- Afișează istoric (cronologic, fără dubluri) ----------
for role, content in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(content)

# ---------- Input nou ----------
prompt = st.chat_input("Întreabă despre cărți, teme sau cere recomandări…")

if prompt:
    # 1) arată mesajul curent al utilizatorului (fără să-l bagi încă în istoric)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) calculează răspunsul și afișează-l
    with st.chat_message("assistant"):
        with st.spinner("Gândesc…"):
            try:
                answer = call_llm(prompt, top_k=top_k, temperature=temperature)
            except Exception as e:
                answer = f"Eroare: {e}"
        st.markdown(answer)

    # 3) persistă runda în istoric și rerulează aplicația
    st.session_state.chat.append(("user", prompt))
    st.session_state.chat.append(("assistant", answer))
    st.rerun()

if voice_out and st.session_state.chat:
    last_role, last_msg = st.session_state.chat[-1]
    if last_role == "assistant" and last_msg:
        # folosește un cache simplu ca să nu regenerezi TTS la fiecare rerulare
        key = hash(last_msg)
        if st.session_state.get("tts_key") != key:
            try:
                st.session_state["tts_audio"] = say(last_msg[:1200])  # taie textul dacă e prea lung
                st.session_state["tts_key"] = key
            except Exception as e:
                st.session_state["tts_audio"] = None
                st.warning(f"Nu am putut genera TTS: {e}")
        # dacă avem audio în cache, îl redăm la fiecare rerandare
        if st.session_state.get("tts_audio"):
            st.audio(st.session_state["tts_audio"], format="audio/mp3")