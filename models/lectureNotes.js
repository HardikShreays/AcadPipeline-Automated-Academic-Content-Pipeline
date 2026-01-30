import mongoose from "mongoose";

const LectureNotesSchema = new mongoose.Schema(
  {
    lectureHash: {
      type: String,
      required: true,
      index: true,
      unique: true,
    },
    notes: {
      type: String,
      required: true,
    },
    pdfUrl: {
      type: String,
      default: null,
    },
    m3u8Url: {
      type: String,
      default: null,
    },
    generatedAt: {
      type: Date,
      default: Date.now,
    },
  },
  {
    strict: true,
    timestamps: true,
  }
);

export default mongoose.model("LectureNotes", LectureNotesSchema);
