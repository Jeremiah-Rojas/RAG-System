"""
RAG System Backend — Flask + OpenAI Embeddings + NumPy Vector Search
======================================================================
Setup with: 
Run with:  python app.py
Stop with: Ctrl+C  (or close the terminal)
"""

import os
import json
import math
import uuid
import pickle
import hashlib
import requests
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# ── document parsers ──────────────────────────────────────────────────────────
from pypdf import PdfReader
from docx import Document as DocxDocument

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG  —  all paths are anchored to the folder that contains app.py,
#            so the server works correctly no matter which directory you
#            launch it from.
# ═════════════════════════════════════════════════════════════════════════════
BASE_DIR     = Path(__file__).parent.resolve()   # ← always the rag_system/ folder
UPLOAD_DIR   = BASE_DIR / "uploads"
INDEX_FILE   = BASE_DIR / "rag_index.pkl"        # persisted on disk
CHUNK_SIZE   = 600          # characters per chunk
CHUNK_OVERLAP = 100         # overlap between chunks
EMBED_MODEL  = "text-embedding-3-small"
CHAT_MODEL   = "gpt-4o-mini"                  # change to gpt-4o if preferred
TOP_K        = 6            # how many chunks to send as context
MAX_TOKENS_ANSWER = 1024

UPLOAD_DIR.mkdir(exist_ok=True)

STATIC_DIR   = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024   # 64 MB upload cap

# ─── In-memory vector store ───────────────────────────────────────────────────
# Structure: { "doc_id": { "filename": str, "chunks": [str], "embeddings": np.ndarray } }
vector_store: dict = {}

# ─── Load persisted index if it exists ───────────────────────────────────────
if INDEX_FILE.exists():
    try:
        with open(INDEX_FILE, "rb") as f:
            vector_store = pickle.load(f)
        print(f"[RAG] Loaded index with {len(vector_store)} document(s) from disk.")
    except Exception as e:
        print(f"[RAG] Could not load index: {e}")

def save_index():
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(vector_store, f)


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def get_api_key(req=None):
    """Return API key from request header or environment variable."""
    if req:
        key = req.headers.get("X-OpenAI-Key", "").strip()
        if key:
            return key
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openai_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def embed_texts(texts: list[str], api_key: str) -> np.ndarray:
    """Call OpenAI Embeddings API; return (N, D) float32 array."""
    url = "https://api.openai.com/v1/embeddings"
    payload = {"model": EMBED_MODEL, "input": texts}
    resp = requests.post(url, headers=openai_headers(api_key), json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    vecs = [item["embedding"] for item in data["data"]]
    return np.array(vecs, dtype="float32")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a: (D,)  b: (N, D) → (N,) similarities."""
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping character-level chunks."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 30]   # drop tiny fragments


def extract_text(filepath: Path) -> str:
    suffix = filepath.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(filepath))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in (".docx", ".doc"):
        doc = DocxDocument(str(filepath))
        return "\n".join(p.text for p in doc.paragraphs)
    elif suffix == ".txt":
        return filepath.read_text(errors="replace")
    elif suffix == ".md":
        return filepath.read_text(errors="replace")
    else:
        # Try plain-text fallback
        try:
            return filepath.read_text(errors="replace")
        except Exception:
            return ""


def get_token_usage(api_key: str) -> dict:
    """
    OpenAI does not expose a real-time credit balance endpoint for pay-as-you-go.
    We track cumulative usage within this session instead.
    Returns usage totals accumulated in the session global below.
    """
    return session_usage.copy()


# Session token tracking (resets each server restart)
session_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "embed_tokens": 0}


def update_usage(usage_dict: dict, embed_tokens: int = 0):
    session_usage["prompt_tokens"]     += usage_dict.get("prompt_tokens", 0)
    session_usage["completion_tokens"] += usage_dict.get("completion_tokens", 0)
    session_usage["total_tokens"]      += usage_dict.get("total_tokens", 0)
    session_usage["embed_tokens"]      += embed_tokens


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/api/validate-key", methods=["POST"])
def validate_key():
    """Check that the API key works by fetching the model list."""
    api_key = get_api_key(request)
    if not api_key:
        return jsonify({"valid": False, "error": "No API key provided."}), 400
    try:
        resp = requests.get(
            "https://api.openai.com/v1/models",
            headers=openai_headers(api_key),
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "error": resp.json().get("error", {}).get("message", "Invalid key.")}), 401
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route("/api/usage", methods=["GET"])
def usage():
    return jsonify(session_usage)


@app.route("/api/documents", methods=["GET"])
def list_documents():
    docs = [
        {"id": doc_id, "filename": info["filename"], "chunks": len(info["chunks"])}
        for doc_id, info in vector_store.items()
    ]
    return jsonify(docs)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    api_key = get_api_key(request)
    if not api_key:
        return jsonify({"error": "No API key provided."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file in request."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    allowed = {".pdf", ".docx", ".doc", ".txt", ".md"}
    suffix  = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        return jsonify({"error": f"Unsupported file type '{suffix}'. Allowed: {', '.join(allowed)}"}), 400

    # Save to disk
    doc_id   = str(uuid.uuid4())[:8]
    savepath = UPLOAD_DIR / f"{doc_id}{suffix}"
    file.save(str(savepath))

    # Extract & chunk
    try:
        raw_text = extract_text(savepath)
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 500

    if not raw_text.strip():
        return jsonify({"error": "File appears empty or unreadable."}), 400

    chunks = chunk_text(raw_text)
    if not chunks:
        return jsonify({"error": "No text chunks extracted from document."}), 400

    # Embed chunks (batch in groups of 100 to stay under API limits)
    try:
        all_embeddings = []
        batch_size = 100
        total_embed_tokens = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            resp = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=openai_headers(api_key),
                json={"model": EMBED_MODEL, "input": batch},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            total_embed_tokens += data.get("usage", {}).get("total_tokens", 0)
            vecs = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(vecs)
        embeddings = np.array(all_embeddings, dtype="float32")
        update_usage({}, embed_tokens=total_embed_tokens)
    except Exception as e:
        return jsonify({"error": f"Embedding failed: {e}"}), 500

    vector_store[doc_id] = {
        "filename": file.filename,
        "chunks": chunks,
        "embeddings": embeddings,
    }
    save_index()

    return jsonify({
        "id": doc_id,
        "filename": file.filename,
        "chunks": len(chunks),
        "embed_tokens_used": total_embed_tokens,
    })


@app.route("/api/delete/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    if doc_id not in vector_store:
        return jsonify({"error": "Document not found."}), 404
    del vector_store[doc_id]
    save_index()
    return jsonify({"deleted": doc_id})


@app.route("/api/query", methods=["POST"])
def query():
    api_key = get_api_key(request)
    if not api_key:
        return jsonify({"error": "No API key provided."}), 400

    body = request.get_json(silent=True) or {}
    user_prompt = (body.get("prompt") or "").strip()
    if not user_prompt:
        return jsonify({"error": "Empty prompt."}), 400

    if not vector_store:
        return jsonify({"error": "No documents loaded. Please upload at least one file first."}), 400

    # 1. Embed the query
    try:
        q_resp = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=openai_headers(api_key),
            json={"model": EMBED_MODEL, "input": [user_prompt]},
            timeout=30,
        )
        q_resp.raise_for_status()
        q_data = q_resp.json()
        q_embed = np.array(q_data["data"][0]["embedding"], dtype="float32")
        embed_tokens = q_data.get("usage", {}).get("total_tokens", 0)
        update_usage({}, embed_tokens=embed_tokens)
    except Exception as e:
        return jsonify({"error": f"Query embedding failed: {e}"}), 500

    # 2. Retrieve top-K chunks across all documents
    scored = []
    for doc_id, info in vector_store.items():
        sims = cosine_similarity(q_embed, info["embeddings"])
        for idx, sim in enumerate(sims):
            scored.append({
                "score": float(sim),
                "chunk": info["chunks"][idx],
                "filename": info["filename"],
                "doc_id": doc_id,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored[:TOP_K]

    # 3. Build context block
    context_parts = []
    for i, item in enumerate(top_chunks, 1):
        context_parts.append(
            f"[Source {i}: {item['filename']}]\n{item['chunk']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = (
        "You are a precise document assistant. "
        "Answer the user's question using ONLY the provided document excerpts below. "
        "Be succinct and cite which document each piece of information comes from. "
        "If the answer cannot be found in the excerpts, say so explicitly — do not guess or use outside knowledge.\n\n"
        f"DOCUMENT EXCERPTS:\n\n{context}"
    )

    # 4. Call chat completion
    try:
        chat_resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=openai_headers(api_key),
            json={
                "model": CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "max_tokens": MAX_TOKENS_ANSWER,
                "temperature": 0.2,
            },
            timeout=60,
        )
        chat_resp.raise_for_status()
        chat_data = chat_resp.json()
    except Exception as e:
        return jsonify({"error": f"Chat completion failed: {e}"}), 500

    usage_info = chat_data.get("usage", {})
    update_usage(usage_info)

    answer = chat_data["choices"][0]["message"]["content"].strip()
    sources = list({item["filename"] for item in top_chunks})

    return jsonify({
        "answer": answer,
        "sources": sources,
        "usage": {
            "this_call": usage_info,
            "session_total": session_usage.copy(),
        },
    })


# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═"*60)
    print("  RAG System — starting on http://127.0.0.1:5000")
    print("  Open that URL in your browser to begin.")
    print("  Press Ctrl+C here to stop the server.")
    print("═"*60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
