/**
 * API server: exposes the overall pipeline (PDF + lecture → notes in MongoDB).
 *
 * Endpoints:
 *   POST /api/pipeline  – Run pipeline. Body: { pdfUrl, m3u8Url, lectureHash? }
 *   GET  /api/notes/:lectureHash – Get notes for a lecture hash (from MongoDB)
 *
 * Start: node server.js
 * Port: process.env.PORT or 3000
 */

import express from "express";
import mongoose from "mongoose";
import { configDotenv } from "dotenv";
import { runOverallPipeline } from "./overall_pipeline.js";
import LectureNotes from "./models/lectureNotes.js";
import { cleanupTempFiles, cleanupAllTempFiles } from "./cleanup.js";

configDotenv();

const app = express();
const PORT = process.env.PORT || 3000;

async function connectDB() {
  if (!process.env.MONGO_URI) {
    throw new Error('Missing MONGO_URI in .env');
  }
  await mongoose.connect(process.env.MONGO_URI);
  console.log("MongoDB connected");
}

app.use(express.json());

// ---------- POST /api/pipeline – run the pipeline ----------
app.post("/api/pipeline", async (req, res) => {
  const { pdfUrl, m3u8Url, lectureHash } = req.body || {};

  if (!pdfUrl || !m3u8Url) {
    return res.status(400).json({
      error: "Missing required fields",
      required: ["pdfUrl", "m3u8Url"],
      optional: ["lectureHash"],
    });
  }

  try {
    const result = await runOverallPipeline(
      pdfUrl,
      m3u8Url,
      lectureHash || null
    );

    return res.status(200).json({
      lectureHash: result.lectureHash,
      notes: result.notes,
      skipped: result.skipped === true,
      generatedAt: result.doc?.generatedAt,
    });
  } catch (err) {
    console.error("Pipeline error:", err?.message || err);
    return res.status(500).json({
      error: err?.message || "Pipeline failed",
    });
  }
});

// ---------- GET /api/notes/:lectureHash – get notes by hash ----------
app.get("/api/notes/:lectureHash", async (req, res) => {
  const { lectureHash } = req.params;

  if (!lectureHash) {
    return res.status(400).json({ error: "lectureHash is required" });
  }

  try {
    const doc = await LectureNotes.findOne({ lectureHash });

    if (!doc) {
      return res.status(404).json({
        error: "Not found",
        lectureHash,
      });
    }

    return res.status(200).json({
      lectureHash: doc.lectureHash,
      notes: doc.notes,
      pdfUrl: doc.pdfUrl,
      m3u8Url: doc.m3u8Url,
      generatedAt: doc.generatedAt,
    });
  } catch (err) {
    console.error("Fetch notes error:", err?.message || err);
    return res.status(500).json({
      error: err?.message || "Failed to fetch notes",
    });
  }
});

// ---------- Cleanup temp files (audios, pdfs) ----------
// POST /api/cleanup  body: { lectureHash: "..." }  or  { all: true }
app.post("/api/cleanup", (req, res) => {
  const { lectureHash, all } = req.body || {};

  if (all === true) {
    const { removed, errors } = cleanupAllTempFiles();
    return res.status(200).json({
      cleaned: "all",
      removedCount: removed.length,
      removed,
      errors: errors.length ? errors : undefined,
    });
  }

  if (!lectureHash || typeof lectureHash !== "string") {
    return res.status(400).json({
      error: "Provide body: { lectureHash: \"...\" } or { all: true }",
    });
  }

  const { removed, errors } = cleanupTempFiles(lectureHash);
  return res.status(200).json({
    lectureHash,
    removedCount: removed.length,
    removed,
    errors: errors.length ? errors : undefined,
  });
});

// ---------- Health check ----------
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`API server listening on port ${PORT}`);
      console.log(`  POST /api/pipeline  – run pipeline (body: { pdfUrl, m3u8Url, lectureHash? })`);
      console.log(`  GET  /api/notes/:lectureHash – get notes`);
      console.log(`  POST /api/cleanup – cleanup temp files (body: { lectureHash } or { all: true })`);
      console.log(`  GET  /health – health check`);
    });
  })
  .catch((err) => {
    console.error("Failed to start server:", err.message);
    process.exit(1);
  });
