import mongoose from "mongoose";
import { configDotenv } from "dotenv";
import Course from "./models/courses.js";
import Lecture from "./models/lectures.js";
import extractAudio from './audio processing/audio_extraction.js'
import { chunkAudio } from "./audio processing/chunking.js";


configDotenv();

async function connectDB() {
  try {
    await mongoose.connect(process.env.MONGO_URI);

    const state = mongoose.connection.readyState;
    // 0 = disconnected, 1 = connected, 2 = connecting, 3 = disconnecting

    if (state !== 1) {
      throw new Error("MongoDB not connected");
    }

    console.log("MongoDB connected");
  } catch (err) {
    console.error("MongoDB connection failed:", err.message);
    process.exit(1);
  }
}


async function allCourses() {
  try {
    const response = await fetch(
      "https://my.newtonschool.co/api/v2/course/h/qofnhrllarxw/learning_course/all/?pagination=false",
      {
        method: "GET",
        headers: {
          Authorization: "Bearer vjAwgKAWgpLkI6DCuNbxl18jND9wKK",
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Courses data:", data);

    // Handle response - it might be an array or an object with a data property
    const courses = Array.isArray(data) ? data : data.data || data.results || [data];
    
    if (courses.length === 0) {
      console.log("No courses to insert");
      return;
    }

    const ack = await Course.insertMany(courses);
    console.log(`Successfully inserted ${ack.length} courses`);
    return ack;
  } catch (error) {
    console.error("Error fetching or inserting courses:", error.message);
    throw error;
  }
}


async function all_lectures() {
  try {
    const courses = await Course.find();
    console.log(`Found ${courses.length} courses to process`);

    for (const course of courses) {
      try {
        // Check if course has a hash property
        if (!course.hash) {
          console.log(`Skipping course ${course._id || course.id}: no hash property`);
          continue;
        }

        const response = await fetch(
          `https://my.newtonschool.co/api/v1/course/h/${course.hash}/lecture/all/?past=true&limit=500`,
          {
            method: "GET",
            headers: {
              Authorization: "Bearer vjAwgKAWgpLkI6DCuNbxl18jND9wKK",
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          console.error(`HTTP error for course ${course.hash}! status: ${response.status}`);
          continue;
        }

        const data = await response.json();
        
        // Handle response - it might be an array or an object with a results/data property
        const lectures = Array.isArray(data) 
          ? data 
          : data.results || data.data || (data.lectures ? [data.lectures] : []);
        
        if (lectures.length === 0) {
          console.log(`No lectures found for course ${course.hash}`);
          continue;
        }

        console.log(`Found ${lectures.length} lectures for course ${course.hash}`);

        const ack = await Lecture.insertMany(lectures);
        console.log(`Successfully inserted ${ack.length} lectures for course ${course.hash}`);
      } catch (error) {
        console.error(`Error processing course ${course.hash || course._id}:`, error.message);
        // Continue with next course instead of stopping
        continue;
      }
    }
    
    console.log("Finished processing all courses for lectures");
  } catch (error) {
    console.error("Error in all_lectures function:", error.message);
    throw error;
  }
}





async function main() {
    // await connectDB();
    await extractAudio({
      m3u8Url: "https://d3dyfaf3iutrxo.cloudfront.net/newton-school-upgrad-recordings/10610714_hls/10610714_master.m3u8",
      outputDir: "audios",
      lectureId: "check"
    })
    console.log(await chunkAudio({
      inputWav: './audios/check.wav',
      outputDir: './audios/chunks',
      duration: 10801,
      chunkSize: 600,  // optional, defaults to 600
      overlap: 5       // optional, defaults to 5
    }))

  process.exit(0);
}

main();