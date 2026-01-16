## Summariser (WIP)

This repository is **under active development**. Current focus is building a pipeline to:

- **Extract lecture audio** from an HLS (`.m3u8`) URL (limited to **1.5 hours**)
- **Chunk audio** into ~10 minute segments
- **Transcribe** each chunk (Whisper / faster-whisper)
- **Post-process / normalize** transcript text (subject-aware prompts)
- **Store results** in MongoDB (`ProcessedLecture` collection)

---

## Current status

- **Works end-to-end** for: extract → chunk → transcribe → post-process → save processed chunks
- Still evolving: schema conventions, error handling, performance, and config cleanup

---

## Tech stack

- **Node.js** (ESM modules) + **Mongoose**
- **ffmpeg** via `fluent-ffmpeg` + `ffmpeg-static`
- **Python** virtual environment for transcription:
  - `audio processing/whisper-env/`
  - `faster-whisper` + its dependencies
- OpenRouter API for transcript cleaning:
  - `OPENROUTER_KEY` required

---

## Environment variables

Create a `.env` in the project root:

```bash
MONGO_URI="mongodb://..."
OPENROUTER_KEY="..."
```

---

## Installation

### Node dependencies

```bash
npm install
```

### Python environment (transcription)

This repo expects a Python venv at:

- `audio processing/whisper-env/bin/python3`

If it already exists, you’re good. Otherwise, create one and install deps inside it.

---

## Main pipeline (lecture processing)

### What it does

The orchestrator is `audio processing/process_lecture.js`:

- Requires:
  - `lectureHash` (identifier for DB + filenames)
  - `m3u8Url` (explicitly provided; **not** derived from hash)
- Extracts only **1.5 hours** of audio (hard-limited in `audio processing/audio_extraction.js`)
- Saves processed results to MongoDB model:
  - `models/processedLectures.js` (`ProcessedLecture`)

### Run example

Edit values in `process_lecture_example.js` and run:

```bash
node process_lecture_example.js
```

Outputs:
- `audios/<lectureHash>.wav`
- `audios/chunks/<lectureHash>/chunk_0.wav`, ...
- MongoDB: `ProcessedLecture` document with `lectureHash` and `processedChunks[]`

---

## View processed lecture (merge chunks)

You can query MongoDB and merge chunk text by `lectureHash` using a small script (example code used in `tempCodeRunnerFile.js`).

Typical workflow:
- Fetch `ProcessedLecture` by `{ lectureHash }`
- Sort `processedChunks` by `chunkNumber`
- Merge text with `\n\n`

---

## Download whiteboard PDF

Use `download_whiteboard_pdf.js` to download a PDF and save it as `<lectureHash>.pdf`.

```bash
node download_whiteboard_pdf.js <lectureHash> "<pdfUrl>" [outputDir]
```

Example:

```bash
node download_whiteboard_pdf.js 10610714 "https://d3dyfaf3iutrxo.cloudfront.net/file/course/video_session/whiteboard/5503ad2946d049c39ea2f139fbd58060.pdf" pdfs
```

Saves:
- `pdfs/10610714.pdf`

---

## Notes / gotchas

- **Network required**:
  - Downloading `.m3u8` / audio segments
  - OpenRouter post-processing calls
  - PDF downloading
- **Last chunk may be skipped** if transcription/post-processing produces empty text (silence / low-entropy filtering).
- The `Lecture` model in `models/lectures.js` is used for **metadata** (raw API data); processed transcripts are stored separately in `ProcessedLecture`.

---

## Roadmap (short-term)

- Improve reliability & retries around transcription + OpenRouter calls
- Better progress tracking and chunk-level error reporting
- Optional: store raw transcripts separately from cleaned transcripts
- Add CLI wrappers for common workflows

