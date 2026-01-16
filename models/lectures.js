import mongoose from "mongoose";
const Lecture = new mongoose.Schema(
    {},
    { strict: false, timestamps: true }
  );
  
  export default mongoose.model("Lectures", Lecture);
  