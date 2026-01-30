/**
 * Overall Pipeline: PDF URL + Lecture Video URL → Combined Notes
 * 
 * This pipeline combines:
 * 1. PDF processing pipeline (downloads PDF, extracts text)
 * 2. Lecture processing pipeline (extracts audio, transcribes, post-processes)
 * 3. Note generation (combines PDF and lecture transcript using LLM)
 * 
 * Usage:
 *   node overall_pipeline.js <pdfUrl> <m3u8Url> [lectureHash]
 * 
 * - pdfUrl: URL to the PDF file
 * - m3u8Url: URL to the lecture video (m3u8 format)
 * - lectureHash: Optional. If omitted, uses timestamp
 * 
 * Notes are saved to MongoDB (LectureNotes collection), indexed by lectureHash.
 * 
 * Example:
 *   node overall_pipeline.js "https://.../whiteboard.pdf" "https://.../master.m3u8" 10610714
 * 
 * Requires:
 * - OPENROUTER_KEY in .env
 * - MONGO_URI in .env
 */

import { configDotenv } from "dotenv";
import mongoose from "mongoose";
import { processPdf } from "./PDF_processing/pdf_pipeline.js";
import { processLecture } from "./audio processing/process_lecture.js";
import ProcessedLecture from "./models/processedLectures.js";
import LectureNotes from "./models/lectureNotes.js";

configDotenv();

const SYSTEM_PROMPT = `You are an academic note generation engine.

INPUTS:
- A lecture PDF (authoritative source of syllabus, structure, and definitions).
- A cleaned lecture transcript (secondary source with instructor emphasis).

ABSOLUTE AUTHORITY RULES (MANDATORY):
1. The PDF is the SINGLE source of truth for:
   - Topics
   - Structure
   - Definitions
   - Scope
2. The lecture transcript is SECONDARY and may ONLY:
   - Emphasize importance
   - Clarify existing PDF concepts
   - Add exam-oriented hints explicitly stated by the instructor
3. If the lecture introduces a topic not present in the PDF, IGNORE IT.
4. If the lecture contradicts the PDF, IGNORE THE LECTURE.
5. Do NOT invent topics, examples, definitions, steps, or syllabus structure.

STRUCTURE RULES:
- Follow the PDF's section order exactly.
- Do NOT create new headings.
- Do NOT reorder content.
- Each output section must correspond to a PDF section.

CONTENT RULES:
- Summarize the PDF content first.
- Inject lecture insights ONLY if they clearly reinforce the same PDF section.
- Do NOT merge unrelated lecture explanations.
- Do NOT generalize beyond what is explicitly stated.

STYLE RULES:
- Clean academic notes.
- Concise, exam-oriented language.
- No conversational tone.
- No references to "lecture", "teacher", or "instructor".
- No implementation narration unless present in the PDF.

FAILURE CONDITIONS (DO NOT VIOLATE):
- Including lecture-only topics
- Letting lecture redefine structure
- Hallucinating examples or explanations
- Mixing multiple PDF sections together

OUTPUT:
Structured notes strictly aligned to the PDF, enhanced only where the lecture explicitly adds value.`;

// ---------- Connect to MongoDB ----------
async function connectDB() {
  if (!process.env.MONGO_URI) {
    throw new Error('Missing env var: MONGO_URI (set it in ".env")');
  }
  await mongoose.connect(process.env.MONGO_URI);
  const state = mongoose.connection.readyState;
  if (state !== 1) throw new Error("MongoDB not connected");
  console.log("MongoDB connected");
}

// ---------- Get lecture transcript from processed chunks ----------
async function getLectureTranscript(lectureHash) {
  const processedLecture = await ProcessedLecture.findOne({ lectureHash });
  
  if (!processedLecture || !processedLecture.processedChunks || processedLecture.processedChunks.length === 0) {
    throw new Error(`No processed lecture found for lectureHash=${lectureHash}`);
  }
  
  // Sort chunks by chunkNumber and merge text
  const sortedChunks = processedLecture.processedChunks
    .slice()
    .sort((a, b) => a.chunkNumber - b.chunkNumber);
  
  const transcript = sortedChunks.map((chunk) => chunk.text).join("\n\n");
  return transcript;
}

// ---------- OpenRouter LLM call ----------
async function callOpenRouter(message, systemPrompt, model = "tngtech/deepseek-r1t2-chimera:free") {
  const apiKey = process.env.OPENROUTER_KEY;
  if (!apiKey) throw new Error("OPENROUTER_KEY not set in .env");
  
  const messages = [];
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push({ role: "user", content: message });
  
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model, messages }),
  });
  
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`OpenRouter API error: ${res.status} ${res.statusText} - ${errText}`);
  }
  
  const data = await res.json();
  const content = data?.choices?.[0]?.message?.content;
  if (content == null) throw new Error("OpenRouter: no content in response");
  
  return content;
}

// ---------- Main pipeline function ----------
async function runOverallPipeline(pdfUrl, m3u8Url, lectureHash = null) {
  // Generate lectureHash from timestamp if not provided
  const hash = lectureHash || Date.now().toString();
  
  try {
    // Connect to MongoDB
    await connectDB();

    // Skip if notes already exist for this hash
    const existingNotes = await LectureNotes.findOne({ lectureHash: hash });
    if (existingNotes && existingNotes.notes) {
      console.log("\n=== Skipping (already processed) ===");
      console.log(`Lecture Hash: ${hash} already has notes in MongoDB. Skipping pipeline.\n`);
      return { lectureHash: hash, notes: existingNotes.notes, doc: existingNotes, skipped: true };
    }

    console.log("\n=== Starting Overall Pipeline ===");
    console.log(`Lecture Hash: ${hash}`);
    console.log(`PDF URL: ${pdfUrl}`);
    console.log(`Lecture URL: ${m3u8Url}\n`);

    // Step 1: Process PDF
    console.log("Step 1/4: Processing PDF...");
    const pdfResult = await processPdf(pdfUrl, hash);
    if (!pdfResult.text?.trim()) {
      throw new Error("PDF produced no text.");
    }
    console.log(`   ✓ Extracted ${pdfResult.text.length} characters from PDF\n`);
    
    // Step 2: Process Lecture (check if already processed)
    console.log("Step 2/4: Processing Lecture...");
    let lectureResult;
    const existingLecture = await ProcessedLecture.findOne({ lectureHash: hash });
    
    if (existingLecture && existingLecture.processedChunks && existingLecture.processedChunks.length > 0) {
      console.log(`   ⚠ Lecture already processed (${existingLecture.processedChunks.length} chunks), skipping...`);
      lectureResult = {
        lectureHash: hash,
        processedChunks: existingLecture.processedChunks.length,
        chunks: existingLecture.processedChunks
      };
    } else {
      lectureResult = await processLecture(hash, m3u8Url);
      console.log(`   ✓ Processed ${lectureResult.processedChunks} chunks`);
    }
    console.log();
    
    // Step 3: Get merged transcript
    console.log("Step 3/4: Retrieving lecture transcript...");
    const lectureText = await getLectureTranscript(hash);
    if (!lectureText?.trim()) {
      throw new Error("Lecture transcript is empty.");
    }
    console.log(`   ✓ Retrieved ${lectureText.length} characters from lecture\n`);
    
    // Step 4: Generate combined notes
    console.log("Step 4/4: Generating combined notes...");
    const userMessage = `PDF CONTENT (AUTHORITATIVE SOURCE):
${pdfResult.text}

---

LECTURE TRANSCRIPT (SECONDARY SOURCE):
${lectureText}

---

Generate structured academic notes following the PDF structure, enhanced only where the lecture explicitly adds value.`;

    const notes = await callOpenRouter(userMessage, SYSTEM_PROMPT);

    // Save to MongoDB (indexed by lectureHash)
    const doc = await LectureNotes.findOneAndUpdate(
      { lectureHash: hash },
      {
        $set: {
          notes,
          pdfUrl: pdfUrl || null,
          m3u8Url: m3u8Url || null,
          generatedAt: new Date(),
        },
      },
      { new: true, upsert: true }
    );
    console.log(`   ✓ Notes saved to MongoDB (lectureHash: ${hash})\n`);
    return { lectureHash: hash, notes, doc };
    
  } finally {
    // Disconnect from MongoDB
    await mongoose.disconnect();
    console.log("MongoDB disconnected");
  }
}

// ---------- CLI ----------
function usage() {
  console.log(`
Usage: node overall_pipeline.js <pdfUrl> <m3u8Url> [lectureHash]

  pdfUrl      URL to the PDF file (e.g. https://.../whiteboard.pdf)
  m3u8Url     URL to the lecture video (m3u8 format, e.g. https://.../master.m3u8)
  lectureHash Optional. If omitted, uses timestamp.

Notes are saved to MongoDB (LectureNotes collection), indexed by lectureHash.

Examples:
  node overall_pipeline.js "https://.../whiteboard.pdf" "https://.../master.m3u8" 10610714
  node overall_pipeline.js "https://.../whiteboard.pdf" "https://.../master.m3u8"

Env: OPENROUTER_KEY and MONGO_URI required in .env file.
`);
}

async function main() {
  const [, , pdfUrl, m3u8Url, lectureHash] = process.argv;

  if (!pdfUrl || !m3u8Url || pdfUrl === "--help" || pdfUrl === "-h") {
    usage();
    process.exit(1);
  }

  try {
    await runOverallPipeline(pdfUrl, m3u8Url, lectureHash || null);
  } catch (err) {
    console.error("✗ Error:", err?.message || err);
    if (err.stack) console.error(err.stack);
    process.exit(1);
  }
}

// Export for programmatic use
export { runOverallPipeline };

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
