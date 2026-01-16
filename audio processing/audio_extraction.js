import ffmpeg from "fluent-ffmpeg";
import ffmpegPath from "ffmpeg-static";
import path from "path";
import fs from "fs";

ffmpeg.setFfmpegPath(ffmpegPath);

export default function extractAudio({
  m3u8Url,
  outputDir,
  lectureId
}) {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const outputPath = path.join(outputDir, `${lectureId}.wav`);

    ffmpeg()
      .input(m3u8Url)
      .inputOptions([
        "-headers", "Referer:https://my.newtonschool.co/\r\n",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5"
      ])

      .noVideo()
      
      // 🔑 LIMIT TO 1.5 HOURS (5400 seconds)
      .duration(5400)

      // 🔑 HARD AUDIO NORMALIZATION
      .audioChannels(1)               // force mono
      .audioFrequency(16000)           // 16kHz
      .audioCodec("pcm_s16le")
      .format("wav")
      .audioFilters([
        {
          filter: "silenceremove",
          options: {
            start_periods: 1,
            start_threshold: "-45dB",
            start_silence: 1.0
          }
        },
        {
          filter: "loudnorm",
          options: {
            I: -16,
            TP: -1.5,
            LRA: 11
          }
        },
        {
          filter: "afade",
          options: {
            t: "in",
            ss: 0,
            d: 0.05
          }
        }
      ])
      

      // 🔑 CRITICAL FOR WHISPER
      .outputOptions([
        "-reset_timestamps", "1",
        "-map_metadata", "-1",
        "-fflags", "+bitexact"
      ])

      .on("start", cmd => console.log(cmd))
      .on("end", () => resolve(outputPath))
      .on("error", reject)
      .save(outputPath);
  });
}
