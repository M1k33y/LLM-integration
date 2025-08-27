import os
from io import BytesIO
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from openai import OpenAI

# Refolosește logica existentă
from app_cli import call_llm   # funcția ta cu RAG+tool

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

client = OpenAI()

import logging
app.logger.setLevel(logging.INFO)

@app.get("/health")
def health():
    app.logger.info("GET /health")
    return "ok", 200


@app.get("/")
def index():
    # doar servește pagina cu chat
    return render_template("index.html")

@app.post("/chat")
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    top_k = int(data.get("top_k", 5))
    temperature = float(data.get("temperature", 0.4))
    if not message:
        return jsonify({"error": "Mesaj gol"}), 400
    try:
        answer = call_llm(message, top_k=top_k, temperature=temperature)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/stt")
def stt():
    from io import BytesIO
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    file = request.files["audio"]
    lang = request.form.get("lang")  # ex: "ro", "en", "es" sau "" pentru auto
    audio_bytes = file.read()
    buf = BytesIO(audio_bytes)
    buf.name = file.filename or "audio.webm"

    # Încercăm gpt-4o-mini-transcribe cu hint de limbă (dacă există)
    try:
        kwargs = {"model": "gpt-4o-mini-transcribe", "file": buf}
        if lang:
            kwargs["language"] = lang  # hint/force language
            # mic bias: pentru română ajută un prompt
            if lang == "ro":
                kwargs["prompt"] = "Transcrie exact în limba română."
        tr = client.audio.transcriptions.create(**kwargs)
        return jsonify({"text": tr.text})
    except Exception:
        # Fallback sigur: whisper-1 (acceptă language + prompt)
        buf.seek(0)
        kwargs = {"model": "whisper-1", "file": buf}
        if lang:
            kwargs["language"] = lang
            if lang == "ro":
                kwargs["prompt"] = "Transcrie exact în limba română."
        tr = client.audio.transcriptions.create(**kwargs)
        return jsonify({"text": tr.text})

@app.post("/tts")
def tts():
    """
    Primește JSON {text: "..."} și întoarce MP3 (audio/mpeg).
    """
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text gol"}), 400

    # generăm TTS ca bytes și îl trimitem ca fișier
    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    audio_bytes = speech.read()
    return send_file(BytesIO(audio_bytes), mimetype="audio/mpeg", download_name="speech.mp3")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Setează OPENAI_API_KEY!")
    app.run(host="0.0.0.0", port=7860, debug=True)
