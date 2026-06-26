# RAG Intelligence System
**Retrieval-Augmented Generation — Local, Private, Document-Grounded**

---

## Files in this folder

```
rag_system/
├── app.py              ← Flask backend (the brain)
├── requirements.txt    ← Python packages needed
├── static/
│   └── index.html      ← Web UI (dark futuristic interface)
├── uploads/            ← Auto-created: stores your uploaded files
└── rag_index.pkl       ← Auto-created: persisted vector index (survives restarts)
```

> **`uploads/`** and **`rag_index.pkl`** are created automatically on first run.
> Do not delete `rag_index.pkl` if you want your documents to persist across server restarts.

---

## One-time setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

If you're on a system with Python 3.12+ or a managed environment:
```bash
pip install --break-system-packages -r requirements.txt
```

### 2. Get your OpenAI API key
- Go to https://platform.openai.com/api-keys
- Create a new secret key
- Copy it (starts with `sk-proj-...`)

---

## Starting the server

```bash
cd rag_system
python app.py
```

You'll see:
```
════════════════════════════════════════════════════════════
  RAG System — starting on http://127.0.0.1:5000
  Open that URL in your browser to begin.
  Press Ctrl+C here to stop the server.
════════════════════════════════════════════════════════════
```

Then open **http://127.0.0.1:5000** in your browser.

---

## Using the system

1. **Paste your OpenAI API key** in the sidebar box → click **Validate Key**
2. **Upload documents** — drag & drop or click the upload zone (PDF, DOCX, TXT, MD)
3. **Ask questions** in the prompt box at the bottom → press Enter or click Send
4. Answers are sourced exclusively from your uploaded documents

### Example prompt
```
According to the PSCI 432 document, how should I perform legal analysis?
```

---

## Stopping the server

Press **Ctrl+C** in the terminal where `app.py` is running.

Your document index is saved automatically to `rag_index.pkl` — it reloads next time you start the server.

---

## Token tracking

- The **top bar** shows total session token usage
- The **stats bar** under the header breaks down: Prompt / Completion / Embed / Total
- Each answer bubble shows per-call token counts

> OpenAI's API charges by token. The embedding model used is `text-embedding-3-small` (cheap).
> Chat completions use `gpt-4o-mini` by default. To use GPT-4o, edit line `CHAT_MODEL` in `app.py`.

---

## Notes

- Your API key is **never stored to disk** — it lives only in memory and is cleared when the server stops
- Documents are chunked into ~600-character overlapping segments for retrieval
- The top 6 most relevant chunks are sent to the LLM for each query
- Supported file types: `.pdf`, `.docx`, `.doc`, `.txt`, `.md`

