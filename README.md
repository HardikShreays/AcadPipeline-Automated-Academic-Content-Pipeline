# AcadPipeline — Automated Academic Content Pipeline

[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)](https://www.mongodb.com/)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](LICENSE)

**AcadPipeline** is a backend pipeline that turns lecture videos and PDFs into structured academic notes. It downloads PDFs, extracts text (with OCR when needed), transcribes lecture audio from HLS streams, and uses an LLM to merge both into exam-oriented notes stored in MongoDB.

---

## Features

- **PDF pipeline** — Download PDF from URL, extract text (pdfplumber + OCR fallback), output by `lectureHash`
- **Lecture pipeline** — Extract audio from m3u8 URL (up to 1.5 hours), chunk, transcribe (faster-whisper), post-process, store in MongoDB
- **Overall pipeline** — Single flow: PDF URL + lecture m3u8 URL → combined notes saved in MongoDB (skips if `lectureHash` already processed)
- **REST API** — Run pipeline, fetch notes by hash, cleanup temp files
- **Temp cleanup** — Auto-cleanup after pipeline run; optional CLI/API to clean by hash or all

---

## Project structure

```
AcadPipeline-Automated-Academic-Content-Pipeline/
├── server.js                 # Express API server (POST /api/pipeline, GET /api/notes, POST /api/cleanup)
├── overall_pipeline.js       # Orchestrator: PDF + lecture → notes in MongoDB (skip if hash exists)
├── cleanup.js                # Temp file cleanup (audios, pdfs) — CLI + exported helpers
├── index.js                  # Scripts: courses/lectures fetch, audio/chunk examples
├── process_lecture_example.js
├── merge_notes.js            # Export merged transcript from ProcessedLecture by hash
├── generate_notes.js         # Legacy: PDF URL + transcript URL → notes (no pipeline)
├── download_whiteboard_pdf.js
│
├── audio processing/         # Lecture → transcript
│   ├── process_lecture.js    # Main: extract → chunk → transcribe → post-process → DB
│   ├── audio_extraction.js   # ffmpeg: m3u8 → wav (1.5h limit)
│   ├── chunking.js           # Split wav into chunks (e.g. 10 min)
│   ├── get_duration.js
│   ├── process_chunk.py      # Transcribe + post-process one chunk (faster-whisper + OpenRouter)
│   ├── post_processing.py
│   ├── transcribe_fw.py
│   └── whisper-env/           # Python venv (transcription) — create locally, not in repo
│
├── PDF_processing/           # PDF → extracted text
│   ├── pdf_pipeline.js       # Download + extract text (exports processPdf, downloadPdf, extractText)
│   ├── download_whiteboard_pdf.js
│   ├── pdf_summariser_ocr.py  # OCR/text extraction
│   ├── pdf_summariser_noocr.py
│   └── pdf_env/              # Python venv (PDF deps, e.g. pdfplumber) — create locally, not in repo
│
├── models/                   # Mongoose schemas
│   ├── processedLectures.js  # lectureHash, processedChunks[], totalChunks, processedAt
│   ├── lectureNotes.js       # lectureHash (indexed), notes, pdfUrl, m3u8Url, generatedAt
│   ├── lectures.js           # Lecture metadata (from external API)
│   └── courses.js            # Course metadata
│
├── openRouter/               # OpenRouter-related utilities (e.g. openrouter.py)
├── .env                      # MONGO_URI, OPENROUTER_KEY (not committed)
├── package.json
└── README.md
```

**Data flow (overall pipeline):**

1. **PDF** — `pdfUrl` → download → extract text (PDF_processing) → text in memory  
2. **Lecture** — `m3u8Url` + `lectureHash` → extract audio → chunk → transcribe → post-process → `ProcessedLecture` in MongoDB  
3. **Notes** — PDF text + merged transcript → LLM (OpenRouter) → notes saved in `LectureNotes` (by `lectureHash`)  
4. **Cleanup** — Temp files (audios, pdfs) for that hash removed after success  

---

## Tech stack

| Layer        | Stack |
|-------------|--------|
| Runtime     | Node.js 18+ (ESM) |
| API         | Express 5 |
| Database    | MongoDB (Mongoose) |
| Audio       | ffmpeg (fluent-ffmpeg, ffmpeg-static), 1.5h cap |
| Transcription | Python: faster-whisper, OpenRouter for post-processing |
| PDF         | Python: pdfplumber, OCR (PDF_processing/pdf_env) |
| LLM         | OpenRouter (e.g. deepseek) for note generation |

---

## Prerequisites

- **Node.js** 18+
- **MongoDB** (local or Atlas)
- **Python 3** (for transcription + PDF OCR)
- **ffmpeg** (on PATH for audio extraction)

---

## Installation

### 1. Clone and install Node dependencies

```bash
git clone https://github.com/HardikShreays/AcadPipeline-Automated-Academic-Content-Pipeline.git
cd AcadPipeline-Automated-Academic-Content-Pipeline
npm install
```

### 2. Environment variables

Create a `.env` file in the project root:

```bash
MONGO_URI="mongodb://localhost:27017/yourdb"   # or your Atlas URI
OPENROUTER_KEY="sk-or-..."
```

Optional: `PORT=3000` (default 3000 for the API server).

### 3. Python environments

**Audio (transcription)** — under `audio processing/`:

```bash
cd "audio processing"
python3 -m venv whisper-env
source whisper-env/bin/activate   # Windows: whisper-env\Scripts\activate
pip install faster-whisper        # and any other deps used by process_chunk.py
deactivate
```

**PDF (OCR / text extraction)** — under `PDF_processing/`:

```bash
cd PDF_processing
python3 -m venv pdf_env
source pdf_env/bin/activate
pip install pdfplumber             # and any other deps for pdf_summariser_ocr.py
deactivate
```

---

## API reference

Start the server:

```bash
npm start
# or: node server.js
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipeline` | Run overall pipeline. Body: `{ "pdfUrl", "m3u8Url", "lectureHash"?: string }`. Returns `{ lectureHash, notes, skipped?, generatedAt }`. Skips if notes already exist for `lectureHash`. |
| `GET`  | `/api/notes/:lectureHash` | Get stored notes for a lecture hash. |
| `POST` | `/api/cleanup` | Clean temp files. Body: `{ "lectureHash": "..." }` or `{ "all": true }`. Returns `{ removedCount, removed[], errors? }`. |
| `GET`  | `/health` | Health check. |

**Example: run pipeline**

```bash
curl -X POST http://localhost:3000/api/pipeline \
  -H "Content-Type: application/json" \
  -d '{"pdfUrl":"https://example.com/slides.pdf","m3u8Url":"https://example.com/lecture.m3u8","lectureHash":"10610714"}'
```

**Example: get notes**

```bash
curl http://localhost:3000/api/notes/10610714
```

---

## CLI usage

**Overall pipeline (PDF + lecture → notes in MongoDB):**

```bash
node overall_pipeline.js "<pdfUrl>" "<m3u8Url>" [lectureHash]
# If lectureHash is omitted, a timestamp is used. If notes exist for hash, pipeline is skipped.
```

**Cleanup temp files (audios, pdfs):**

```bash
# By lecture hash
node cleanup.js 10610714
# Or all
node cleanup.js --all
# Or via npm
npm run cleanup -- 10610714
npm run cleanup -- --all
```

**Lecture-only processing (example):**

```bash
# Edit process_lecture_example.js with lectureHash and m3u8Url, then:
node process_lecture_example.js
```

**PDF-only pipeline:**

```bash
node PDF_processing/pdf_pipeline.js "<pdfUrl>" [lectureHash] [outputDir]
```

---

## Roadmap and future work

- **Current** — Stable backend: pipeline, API, cleanup, MongoDB storage by `lectureHash`.
- **Planned**
  - **Frontend** — A web UI will be added (separate repo or `/frontend` in this repo) to:
    - Submit PDF + lecture URLs and optional `lectureHash`
    - Trigger the pipeline via `POST /api/pipeline`
    - Display status and show generated notes from `GET /api/notes/:lectureHash`
    - List or search lectures/notes (if list/search endpoints are added)
  - **Backend** — Optional: job queue for long-running runs, progress endpoints, list notes/courses.

The API is designed so a frontend can rely on:

- `POST /api/pipeline` to start (or skip) a run
- `GET /api/notes/:lectureHash` to display notes
- `POST /api/cleanup` to free disk space when needed

---

## Notes and gotchas

- **Network** — Pipeline needs internet for: m3u8/audio, PDF download, OpenRouter.
- **Audio limit** — Lecture audio is capped at 1.5 hours.
- **Idempotency** — Same `lectureHash` skips pipeline and returns existing notes; temp files are not re-created.
- **Temp files** — `audios/` and `pdfs/` are ignored in git; cleanup runs after a successful pipeline and can be triggered via API or CLI.

---

## License

ISC.

---

## Author

**HardikShreays**  
GitHub: [HardikShreays](https://github.com/HardikShreays)  
Repository: [AcadPipeline-Automated-Academic-Content-Pipeline](https://github.com/HardikShreays/AcadPipeline-Automated-Academic-Content-Pipeline)
