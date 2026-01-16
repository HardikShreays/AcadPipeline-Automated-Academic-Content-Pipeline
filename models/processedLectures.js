import mongoose from "mongoose";

const ProcessedLectureSchema = new mongoose.Schema(
  {
    lectureHash: {
      type: String,
      required: true,
      index: true,
      unique: true
    },
    processedChunks: [
      {
        chunkNumber: {
          type: Number,
          required: true
        },
        startTime: {
          type: Number,
          required: true
        },
        endTime: {
          type: Number,
          required: true
        },
        text: {
          type: String,
          required: true
        }
      }
    ],
    totalChunks: {
      type: Number,
      default: 0
    },
    processedAt: {
      type: Date,
      default: Date.now
    }
  },
  { 
    strict: true, 
    timestamps: true 
  }
);

export default mongoose.model("ProcessedLecture", ProcessedLectureSchema);
