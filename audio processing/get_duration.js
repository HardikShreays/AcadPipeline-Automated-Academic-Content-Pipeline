import ffmpeg from "fluent-ffmpeg";
import ffmpegPath from "ffmpeg-static";

ffmpeg.setFfmpegPath(ffmpegPath);

/**
 * Get the duration of an audio file in seconds.
 * @param {string} audioPath - Path to the audio file
 * @returns {Promise<number>} Duration in seconds
 */
export function getAudioDuration(audioPath) {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(audioPath, (err, metadata) => {
      if (err) {
        reject(err);
        return;
      }
      
      const duration = metadata.format.duration;
      resolve(duration || 0);
    });
  });
}
