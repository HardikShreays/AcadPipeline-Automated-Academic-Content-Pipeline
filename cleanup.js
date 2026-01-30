/**
 * Clean up temp files: audios (wav + chunks) and pdfs (pdf + extracted txt).
 *
 * - For a lectureHash: removes audios/<hash>.wav, audios/chunks/<hash>/, pdfs/<hash>.pdf, pdfs/<hash>.txt
 * - cleanAll: removes everything under audios/ and pdfs/ (keeps the dirs)
 */

import fs from "fs";
import path from "path";

const AUDIOS_DIR = "audios";
const PDFS_DIR = "pdfs";

function safeRemove(p) {
  try {
    if (fs.existsSync(p)) {
      const stat = fs.statSync(p);
      if (stat.isDirectory()) {
        fs.rmSync(p, { recursive: true });
        return { path: p, removed: true, type: "dir" };
      }
      fs.rmSync(p);
      return { path: p, removed: true, type: "file" };
    }
  } catch (err) {
    return { path: p, removed: false, error: err.message };
  }
  return { path: p, removed: false, reason: "not found" };
}

/**
 * Remove temp files for a single lecture hash.
 * @param {string} lectureHash
 * @returns {{ removed: string[], errors: Array<{ path: string, error: string }> }}
 */
export function cleanupTempFiles(lectureHash) {
  const cwd = process.cwd();
  const removed = [];
  const errors = [];

  const targets = [
    path.join(cwd, AUDIOS_DIR, `${lectureHash}.wav`),
    path.join(cwd, AUDIOS_DIR, "chunks", lectureHash),
    path.join(cwd, PDFS_DIR, `${lectureHash}.pdf`),
    path.join(cwd, PDFS_DIR, `${lectureHash}.txt`),
  ];

  for (const p of targets) {
    const result = safeRemove(p);
    if (result.removed) removed.push(p);
    if (result.error) errors.push({ path: p, error: result.error });
  }

  return { removed, errors };
}

/**
 * Remove all temp files under audios/ and pdfs/.
 * @returns {{ removed: string[], errors: Array<{ path: string, error: string }> }}
 */
export function cleanupAllTempFiles() {
  const cwd = process.cwd();
  const removed = [];
  const errors = [];

  const audiosPath = path.join(cwd, AUDIOS_DIR);
  const pdfsPath = path.join(cwd, PDFS_DIR);

  if (fs.existsSync(audiosPath)) {
    const entries = fs.readdirSync(audiosPath);
    for (const name of entries) {
      const full = path.join(audiosPath, name);
      const result = safeRemove(full);
      if (result.removed) removed.push(full);
      if (result.error) errors.push({ path: full, error: result.error });
    }
  }

  if (fs.existsSync(pdfsPath)) {
    const entries = fs.readdirSync(pdfsPath);
    for (const name of entries) {
      const full = path.join(pdfsPath, name);
      const result = safeRemove(full);
      if (result.removed) removed.push(full);
      if (result.error) errors.push({ path: full, error: result.error });
    }
  }

  return { removed, errors };
}

// ---------- CLI ----------
// node cleanup.js <lectureHash>   or   node cleanup.js --all
if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , arg] = process.argv;
  if (!arg || arg === "--help" || arg === "-h") {
    console.log("Usage: node cleanup.js <lectureHash> | --all");
    console.log("  lectureHash  – remove temp files for this hash (audios, pdfs)");
    console.log("  --all        – remove all temp files under audios/ and pdfs/");
    process.exit(1);
  }
  if (arg === "--all") {
    const { removed, errors } = cleanupAllTempFiles();
    console.log(`Removed ${removed.length} item(s)`);
    if (errors.length) console.warn("Errors:", errors);
    process.exit(errors.length ? 1 : 0);
  }
  const { removed, errors } = cleanupTempFiles(arg);
  console.log(`Removed ${removed.length} item(s) for ${arg}`);
  if (errors.length) console.warn("Errors:", errors);
  process.exit(errors.length ? 1 : 0);
}
