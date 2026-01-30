import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function usage() {
  console.log(
    [
      "Usage:",
      "  node pdf_pipeline.js <pdfUrl> [lectureHash] [outputDir]",
      "",
      "Example:",
      '  node pdf_pipeline.js "https://example.com/document.pdf"',
      '  node pdf_pipeline.js "https://example.com/document.pdf" 10610714',
      '  node pdf_pipeline.js "https://example.com/document.pdf" 10610714 pdfs',
      "",
      "Notes:",
      "- Downloads PDF from URL",
      "- Extracts text using OCR if needed",
      "- Saves extracted text to <outputDir>/<lectureHash>.txt",
      "- If lectureHash is not provided, uses timestamp",
    ].join("\n")
  );
}

export async function downloadPdf(pdfUrl, lectureHash, outputDir) {
  const downloadScript = path.join(__dirname, "download_whiteboard_pdf.js");
  const outDir = outputDir || "pdfs";
  
  // Ensure output directory exists
  const outDirPath = path.join(process.cwd(), outDir);
  fs.mkdirSync(outDirPath, { recursive: true });
  
  const command = `node "${downloadScript}" "${lectureHash}" "${pdfUrl}" "${outDir}"`;
  
  console.log(`Downloading PDF from: ${pdfUrl}`);
  const { stdout, stderr } = await execAsync(command);
  
  if (stderr) {
    console.warn("Download warnings:", stderr);
  }
  
  const pdfPath = path.join(process.cwd(), outDir, `${lectureHash}.pdf`);
  return pdfPath;
}

export async function extractText(pdfPath, outputPath) {
  const pythonScript = path.join(__dirname, "pdf_summariser_ocr.py");

  // Use dedicated PDF venv: PDF_processing/pdf_env
  const venvPythonPath = path.join(__dirname, "pdf_env", "bin", "python3");

  console.log(`Extracting text from: ${pdfPath}`);

  if (!fs.existsSync(venvPythonPath)) {
    throw new Error(
      `Python venv not found at ${venvPythonPath}. ` +
      `Create the virtual environment there (named pdf_env) with required PDF OCR deps or update pdf_pipeline.js to point to your PDF OCR venv.`
    );
  }

  const command = `"${venvPythonPath}" "${pythonScript}" "${pdfPath}" "${outputPath}"`;

  try {
    const { stdout, stderr } = await execAsync(command);

    if (stderr && !stderr.includes("Extracted text saved to")) {
      console.warn("Extraction warnings:", stderr);
    }

    if (stdout) {
      console.log(stdout);
    }

    return outputPath;
  } catch (error) {
    throw new Error(`PDF OCR failed. Original error: ${error.message}`);
  }
}

export async function processPdf(pdfUrl, lectureHash, outputDir) {
  // Generate lectureHash from timestamp if not provided
  const hash = lectureHash || Date.now().toString();
  const outDir = outputDir || "pdfs";
  
  // Step 1: Download PDF
  const pdfPath = await downloadPdf(pdfUrl, hash, outDir);
  console.log(`PDF downloaded to: ${pdfPath}`);
  
  // Step 2: Extract text and save to file
  const outputPath = path.join(process.cwd(), outDir, `${hash}.txt`);
  await extractText(pdfPath, outputPath);
  
  // Step 3: Read extracted text
  const pdfText = fs.readFileSync(outputPath, "utf8");
  
  return {
    lectureHash: hash,
    pdfPath,
    textPath: outputPath,
    text: pdfText
  };
}

async function main() {
  const [, , pdfUrl, lectureHash, outputDir] = process.argv;
  
  if (!pdfUrl) {
    usage();
    process.exit(1);
  }
  
  try {
    const result = await processPdf(pdfUrl, lectureHash, outputDir);
    console.log(`\nPipeline completed successfully!`);
    console.log(`PDF: ${result.pdfPath}`);
    console.log(`Extracted text: ${result.textPath}`);
  } catch (error) {
    console.error("Pipeline error:", error.message);
    if (error.stdout) console.error("Stdout:", error.stdout);
    if (error.stderr) console.error("Stderr:", error.stderr);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err?.stack || String(err));
  process.exit(1);
});
