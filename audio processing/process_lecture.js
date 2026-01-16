import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";
import extractAudio from "./audio_extraction.js";
import { chunkAudio } from "./chunking.js";
import { getAudioDuration } from "./get_duration.js";
import ProcessedLecture from "../models/processedLectures.js";

const execAsync = promisify(exec);

/**
 * Process a single audio chunk using Python script
 * @param {string} chunkPath - Path to the audio chunk
 * @returns {Promise<string>} Processed text
 */
async function processChunkPython(chunkPath) {
  const audioProcessingDir = path.join(process.cwd(), "audio processing");
  const scriptPath = path.join(audioProcessingDir, "process_chunk.py");
  const venvPythonPath = path.join(audioProcessingDir, "whisper-env", "bin", "python3");
  
  // Use virtual environment Python if it exists, otherwise fall back to system python3
  const pythonCmd = fs.existsSync(venvPythonPath) ? venvPythonPath : "python3";
  
  try {
    // Change to audio processing directory so imports work correctly
    const { stdout, stderr } = await execAsync(
      `cd "${audioProcessingDir}" && "${pythonCmd}" "process_chunk.py" "${chunkPath}"`
    );
    
    if (stderr && !stderr.includes("WARNING")) {
      console.error(`Python stderr for ${chunkPath}:`, stderr);
    }
    
    return stdout.trim();
  } catch (error) {
    console.error(`Error processing chunk ${chunkPath}:`, error.message);
    throw error;
  }
}

/**
 * Process a complete lecture: extract, chunk, transcribe, and post-process
 * @param {string} lectureHash - The lecture hash/ID (used to identify the lecture in the database)
 * @param {string} m3u8Url - The m3u8 URL for the lecture (must be provided explicitly)
 * @returns {Promise<Object>} Processing results
 */
export async function processLecture(lectureHash, m3u8Url) {
  try {
    if (!m3u8Url) {
      throw new Error("m3u8Url is required");
    }

    console.log(`Processing lecture ${lectureHash}...`);
    
    // Step 1: Extract audio (limited to 1.5 hours)
    const outputDir = path.join(process.cwd(), "audios");
    const audioPath = await extractAudio({
      m3u8Url,
      outputDir,
      lectureId: lectureHash
    });
    
    console.log(`Audio extracted to: ${audioPath}`);
    
    // Step 2: Get audio duration
    const duration = await getAudioDuration(audioPath);
    console.log(`Audio duration: ${duration} seconds`);
    
    // Step 3: Chunk the audio
    const chunksDir = path.join(outputDir, "chunks", lectureHash);
    const chunks = await chunkAudio({
      inputWav: audioPath,
      outputDir: chunksDir,
      duration: Math.min(duration, 5400), // Max 1.5 hours
      chunkSize: 600,  // 10 minutes
      overlap: 5       // 5 seconds overlap
    });
    
    console.log(`Created ${chunks.length} chunks`);
    
    // Step 4: Process each chunk (transcribe + post-process)
    const processedChunks = [];
    
    for (const chunk of chunks) {
      console.log(`Processing chunk ${chunk.index}...`);
      try {
        const processedText = await processChunkPython(chunk.path);
        
        if (processedText && processedText.trim()) {
          processedChunks.push({
            chunkNumber: chunk.index,
            startTime: chunk.start,
            endTime: chunk.end,
            text: processedText
          });
          console.log(`Chunk ${chunk.index} processed successfully`);
        } else {
          console.warn(`Chunk ${chunk.index} produced empty or no text, skipping`);
        }
      } catch (error) {
        console.error(`Error processing chunk ${chunk.index}:`, error.message);
        // Continue with other chunks even if one fails
      }
    }
    
    console.log(`Successfully processed ${processedChunks.length} chunks`);
    
    // Step 5: Save processed lecture data to database
    try {
      const processedLecture = await ProcessedLecture.findOneAndUpdate(
        { lectureHash: lectureHash },
        {
          $set: {
            processedChunks: processedChunks,
            processedAt: new Date(),
            totalChunks: processedChunks.length
          }
        },
        { new: true, upsert: true }
      );
      
      console.log(`Processed lecture data saved to database (lectureHash: ${lectureHash})`);
    } catch (dbError) {
      console.error(`Error saving processed lecture to database:`, dbError.message);
      // Don't fail the entire process if DB save fails
    }
    
    return {
      lectureHash,
      audioPath,
      totalChunks: chunks.length,
      processedChunks: processedChunks.length,
      chunks: processedChunks
    };
    
  } catch (error) {
    console.error(`Error processing lecture ${lectureHash}:`, error.message);
    throw error;
  }
}
