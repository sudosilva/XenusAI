<p align="center">
  <h1 align="center">🧠 XenusAI</h1>
  <p align="center"><b>Private Local Knowledge Agent with Voice Interaction</b></p>
  <p align="center">
    A fully local, unrestricted AI agent that absorbs knowledge from any source and answers questions using retrieval-augmented generation (RAG) — with native Speech-to-Text and Text-to-Speech voice capabilities.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/LLM-SmolLM2--360M-green?style=flat-square" />
  <img src="https://img.shields.io/badge/vector_db-ChromaDB-purple?style=flat-square" />
  <img src="https://img.shields.io/badge/GPU-CUDA_Accelerated-red?style=flat-square&logo=nvidia" />
  <img src="https://img.shields.io/badge/voice-STT_%26_TTS-orange?style=flat-square" />
</p>

---

## ✨ Features

- **🔒 100% Local** — No API keys, no cloud. All processing runs on your hardware.
- **🎙️ Voice Agent** — Native Speech-to-Text dictation via OS microphone + autonomous Text-to-Speech responses.
- **📚 Knowledge Ingestion** — Absorbs URLs, PDFs, Markdown, DOCX, CSVs, and entire directories.
- **🧠 RAG Pipeline** — Retrieval-Augmented Generation using ChromaDB vector search + HuggingFace SmolLM2.
- **⚡ GPU Accelerated** — Automatic CUDA detection for PyTorch tensor operations.
- **🌐 Auto-Learning** — Autonomously fetches Wikipedia when confidence is low (AutoFetcher).
- **🖥️ Desktop GUI** — Clean, dark-themed web interface powered by Eel.
- **💬 Conversational AI** — Intent classifier separates casual chat from knowledge queries.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/sudosilva/XenusAI.git
cd XenusAI
pip install -r requirements.txt
```

### 2. Launch the GUI

```bash
python app.py
```

The web interface will open automatically in your default browser at `http://localhost:8147`.

### 3. Launch the CLI (alternative)

```bash
python -m interface.cli
```

---

## 📥 Knowledge Ingestion

Ingest knowledge through the GUI sidebar or the CLI:

| Source Type | Example |
|---|---|
| **URL** | `https://en.wikipedia.org/wiki/Binary_search_algorithm` |
| **File** | `C:\path\to\document.pdf` |
| **Directory** | `C:\path\to\folder\` |

### Supported File Types

`.txt` `.md` `.html` `.pdf` `.docx` `.csv` `.json` `.log`

---

## 🎙️ Voice Interaction

XenusAI includes a full voice pipeline:

- **Speech-to-Text**: Click the microphone button, select your hardware device from the dropdown, speak, and click again to stop. Your speech is transcribed locally via Google Speech Recognition and auto-sent to the AI.
- **Text-to-Speech**: Every AI response is automatically read aloud using your OS's native neural voices. Manual playback is available via the speaker icon on each message.

> Voice processing is handled entirely through Python (`sounddevice` + `SpeechRecognition`), bypassing browser audio sandbox limitations.

---

## 🏗️ Architecture

```
User Input (Text / Voice)
     │
     ▼
┌─────────────────────────┐
│  Intent Classifier       │  ← Greetings skip RAG entirely
│  (retrieval/llm.py)      │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  Vector Search           │  ← ChromaDB cosine similarity
│  (retrieval/search.py)   │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  AutoFetcher             │  ← Wikipedia auto-learning
│  (retrieval/auto_fetcher)│     when confidence < 35%
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  LLM Generation          │  ← HuggingFace SmolLM2-360M
│  (retrieval/generator.py)│     GPU/CPU auto-detection
└─────────────────────────┘
     │
     ▼
  Response (Text + TTS)
```

### Data Pipeline

```
URL/File/Folder → Download → Clean → Chunk (512 tokens) → Embed → ChromaDB
```

---

## 📁 Project Structure

```
XenusAI/
├── app.py                  # Eel GUI application + Voice STT endpoints
├── config.py               # Paths, models, pipeline parameters
├── requirements.txt        # Python dependencies
│
├── interface/              # User interfaces
│   ├── cli.py              # Interactive terminal CLI
│   └── web/                # Eel web frontend
│       ├── index.html      # Application layout
│       ├── style.css        # Dark theme styling
│       └── app.js          # Frontend logic + Voice API
│
├── pipelines/              # Data processing pipeline
│   ├── downloader.py       # URL/file fetching
│   ├── processor.py        # Text cleaning & normalization
│   ├── chunker.py          # Token-based text splitting
│   ├── embedder.py         # Embedding + ChromaDB storage
│   └── ingest.py           # End-to-end ingestion orchestrator
│
├── retrieval/              # Knowledge retrieval & generation
│   ├── search.py           # Vector similarity search
│   ├── llm.py              # Response engine + intent classifier
│   ├── generator.py        # HuggingFace SmolLM2 text generation
│   └── auto_fetcher.py     # Autonomous Wikipedia learning
│
├── scripts/                # Bulk ingestion utilities
│   ├── bulk_ingest.py
│   └── ...
│
└── data/                   # Runtime data (gitignored)
    ├── raw/                # Downloaded source files
    ├── processed/          # Cleaned text
    └── chroma_db/          # Vector database
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence embedding model |
| `CHUNK_SIZE` | `512` | Target tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `LLM_NUM_RESULTS` | `5` | Top-K retrieval results |
| `CHROMA_COLLECTION_NAME` | `xenus_knowledge` | Vector DB collection |

---

## 🖥️ System Requirements

- **Python** 3.10+
- **OS**: Windows 10/11 (primary), Linux/macOS (untested)
- **RAM**: 4GB minimum, 8GB+ recommended
- **GPU**: Optional — CUDA-compatible NVIDIA GPU for acceleration
- **Microphone**: Required for voice features

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
