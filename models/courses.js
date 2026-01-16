import mongoose from "mongoose";
const Course = new mongoose.Schema(
    {},
    { strict: false, timestamps: true }
  );
  
  export default mongoose.model("Course", Course);
  