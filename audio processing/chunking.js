import ffmpeg from "fluent-ffmpeg";
import ffmpegPath from "ffmpeg-static";
import fs from "fs";
import path from "path";

ffmpeg.setFfmpegPath(ffmpegPath);
// chucnking and processig chunks

export async function chunkAudio({
  inputWav,
  outputDir,
  duration,          // seconds (from ffprobe)
  chunkSize = 600,   // 10 min
  overlap = 5
}) {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const chunks = [];
  let start = 0;
  let index = 0;

  while (start < duration) {
    const out = path.join(outputDir, `chunk_${index}.wav`);

    const effectiveDuration = Math.min(
      chunkSize + overlap,
      duration - start
    );

    await new Promise((res, rej) => {
      ffmpeg(inputWav)
        .seekInput(start)
        .duration(effectiveDuration)

        // 🔑 HARD SANITIZATION
        .audioChannels(1)                 // mono
        .audioFrequency(16000)             // 16kHz
        .audioCodec("pcm_s16le")           // Whisper-safe
        .format("wav")

        
      //   .audioFilters([
      //     {
      //       filter: "silenceremove",
      //       options: {
      //         start_periods: 1,
      //         start_threshold: "-45dB",
      //         start_silence: 1.0,
      //         stop_periods: 1,
      //         stop_threshold: "-45dB",
      //         stop_silence: 1.0
      //       }
      //     },
      //     // 2️⃣ loudness normalization
      //     {
      //       filter: "loudnorm",
      //       options: {
      //         I: -16,
      //         TP: -1.5,
      //         LRA: 11
      //       }
      //     },
      //     {
      //       filter: "afade",
      //       options: {
      //         t: "in",
      //         ss: 0,
      //         d: 0.05
      //       }
      //     }
    
      // ])
      // 🔑 TIMESTAMP RESET (CRITICAL)
      .outputOptions([
        "-fflags", "+bitexact",
        "-reset_timestamps", "1",
        "-map_metadata", "-1"
      ])

        .on("end", res)
        .on("error", rej)
        .save(out);
    });

    chunks.push({
      index,
      start,
      end: Math.min(start + chunkSize, duration),
      path: out
    });

    start += chunkSize;
    index++;
  }

  return chunks;
}
