/**
 * Example usage of the lecture processing pipeline
 * 
 * This script demonstrates how to process a lecture using the complete pipeline:
 * 1. Extract audio (limited to 1.5 hours)
 * 2. Chunk the audio
 * 3. Transcribe each chunk
 * 4. Post-process each chunk
 * 5. Update Lecture document in database
 */

import mongoose from "mongoose";
import { configDotenv } from "dotenv";
import { processLecture } from "./audio processing/process_lecture.js";

configDotenv();

async function connectDB() {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    const state = mongoose.connection.readyState;
    if (state !== 1) {
      throw new Error("MongoDB not connected");
    }
    console.log("MongoDB connected");
  } catch (err) {
    console.error("MongoDB connection failed:", err.message);
    process.exit(1);
  }
}

async function main() {
  // Connect to database
  await connectDB();
  
  // Process a lecture by hash
  // The hash is used to identify the lecture in the database
  const lectureHash = "1"; // Replace with actual lecture hash
  const m3u8Url = "https://d3dyfaf3iutrxo.cloudfront.net/newton-school-upgrad-recordings/10604793_hls/10604793_master.m3u8"
  
  try {
    const result = await processLecture(lectureHash, m3u8Url);
    console.log("\n=== Processing Complete ===");
    console.log(`Lecture Hash: ${result.lectureHash}`);
    console.log(`Total Chunks: ${result.totalChunks}`);
    console.log(`Processed Chunks: ${result.processedChunks}`);
    console.log(`Audio Path: ${result.audioPath}`);
  } catch (error) {
    console.error("Error processing lecture:", error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    process.exit(0);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
