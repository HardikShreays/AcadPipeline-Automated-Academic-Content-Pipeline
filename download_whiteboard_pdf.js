import fs from "fs";
import path from "path";
import { pipeline } from "stream/promises";
import { Readable } from "stream";

function usage() {
  console.log(
    [
      "Usage:",
      "  node download_whiteboard_pdf.js <lectureHash> <pdfUrl> [outputDir]",
      "",
      "Example:",
      '  node download_whiteboard_pdf.js 10610714 "https://d3dyfaf3iutrxo.cloudfront.net/file/course/video_session/whiteboard/5503ad2946d049c39ea2f139fbd58060.pdf" pdfs',
      "",
      "Notes:",
      "- Saves as <outputDir>/<lectureHash>.pdf",
      "- Requires Node 18+ (for built-in fetch).",
    ].join("\n")
  );
}

async function downloadPdf({ lectureHash, pdfUrl, outputDir }) {
  if (!lectureHash) throw new Error("lectureHash is required");
  if (!pdfUrl) throw new Error("pdfUrl is required");

  const outDir = outputDir || "pdfs";
  const outPath = path.join(process.cwd(), outDir, `${lectureHash}.pdf`);

  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  const res = await fetch(pdfUrl, {
    method: "GET",
    redirect: "follow",
    headers: {
      // Some CDNs / origins behave better with a UA
      "User-Agent": "Summariser/1.0 (pdf-downloader)",
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to download PDF: ${res.status} ${res.statusText}`);
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("pdf")) {
    // Still allow saving, but warn loudly (sometimes CDNs omit content-type)
    console.warn(`Warning: content-type is "${contentType}" (expected PDF). Saving anyway.`);
  }

  if (!res.body) {
    throw new Error("Response has no body stream");
  }

  // Node fetch returns a web ReadableStream; convert to Node stream for pipeline
  const nodeStream = Readable.fromWeb(res.body);
  await pipeline(nodeStream, fs.createWriteStream(outPath));

  return outPath;
}

async function main() {
  const [, , lectureHash, pdfUrl, outputDir] = process.argv;
  if (!lectureHash || !pdfUrl) {
    usage();
    process.exit(1);
  }

  const outPath = await downloadPdf({ lectureHash, pdfUrl, outputDir });
  console.log(`Saved PDF to: ${outPath}`);
}

main().catch((err) => {
  console.error(err?.stack || String(err));
  process.exit(1);
});

