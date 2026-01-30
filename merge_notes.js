import mongoose from "mongoose";
import { configDotenv } from "dotenv";
import fs from "fs";
import path from "path";
import ProcessedLecture from "./models/processedLectures.js";

configDotenv();

async function connectDB() {
  if (!process.env.MONGO_URI) {
    throw new Error('Missing env var: MONGO_URI (set it in ".env")');
  }
  await mongoose.connect(process.env.MONGO_URI);
  const state = mongoose.connection.readyState;
  if (state !== 1) throw new Error("MongoDB not connected");
}

// Approx: 1 token ≈ 4 characters (rough but useful)
function countTokens(text) {
  return Math.ceil(text.length / 4);
}

function countWords(text) {
  return text.trim().split(/\s+/).filter((w) => w.length > 0).length;
}

async function exportMergedNotesToFile({ lectureHash, outPath }) {
  await connectDB();

  const query = lectureHash ? { lectureHash } : {};
  const processedLectures = await ProcessedLecture.find(query).sort({ processedAt: -1 });

  if (processedLectures.length === 0) {
    throw new Error(
      lectureHash
        ? `No processed lecture found for lectureHash=${lectureHash}`
        : "No processed lectures found"
    );
  }

  const resolvedOutPath =
    outPath ??
    path.join(
      process.cwd(),
      `merged_notes_${lectureHash ?? "all"}_${Date.now()}.txt`
    );

  const writeStream = fs.createWriteStream(resolvedOutPath, { flags: "a" });

  let totalCharacters = 0;
  let totalWords = 0;
  let totalTokens = 0;

  for (const lecture of processedLectures) {
    const sortedChunks = (lecture.processedChunks ?? [])
      .slice()
      .sort((a, b) => a.chunkNumber - b.chunkNumber);

    const mergedText = sortedChunks.map((chunk) => chunk.text).join("\n\n");

    const chars = mergedText.length;
    const words = countWords(mergedText);
    const tokens = countTokens(mergedText);

    totalCharacters += chars;
    totalWords += words;
    totalTokens += tokens;

    writeStream.write(`\n${"=".repeat(80)}\n`);
    writeStream.write(`Lecture Hash: ${lecture.lectureHash}\n`);
    writeStream.write(`Total Chunks: ${lecture.totalChunks}\n`);
    writeStream.write(`Processed At: ${lecture.processedAt}\n`);
    writeStream.write(`Characters: ${chars} | Words: ${words} | Tokens: ${tokens}\n`);
    writeStream.write(`${"=".repeat(80)}\n\n`);
    writeStream.write(mergedText);
    writeStream.write(`\n\n`);
  }

  writeStream.write(`\n\n${"=".repeat(80)}\n`);
  writeStream.write(`SUMMARY\n`);
  writeStream.write(`${"=".repeat(80)}\n`);
  writeStream.write(`Total Lectures: ${processedLectures.length}\n`);
  writeStream.write(`Total Characters: ${totalCharacters}\n`);
  writeStream.write(`Total Words: ${totalWords}\n`);
  writeStream.write(`Total Tokens (approx): ${totalTokens}\n`);
  writeStream.write(`${"=".repeat(80)}\n`);
  writeStream.end();

  return { outPath: resolvedOutPath, totalLectures: processedLectures.length };
}

function printUsageAndExit() {
  // Keep usage short and strict (ESM project; node >= 18 recommended)
  console.log(
    [
      "Usage:",
      "  node merge_notes.js <lectureHash> [outputFile]",
      "",
      "Examples:",
      "  node merge_notes.js 10610714",
      '  node merge_notes.js 10610714 "merged_notes_10610714.txt"',
    ].join("\n")
  );
  process.exit(1);
}

async function main() {
  const [, , lectureHashArg, outPathArg] = process.argv;
  if (!lectureHashArg || lectureHashArg === "--help" || lectureHashArg === "-h") {
    printUsageAndExit();
  }

  const lectureHash = String(lectureHashArg);
  const outPath = outPathArg ? path.resolve(process.cwd(), outPathArg) : undefined;

  const result = await exportMergedNotesToFile({ lectureHash, outPath });
  console.log(`✓ Notes exported to: ${result.outPath}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(err?.message ?? err);
    process.exit(1);
  });
}
