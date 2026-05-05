const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

async function list() {
  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY, { apiVersion: 'v1' });
  try {
    // There is no direct listModels in the main class usually, 
    // it's often a separate client or not exposed in this SDK.
    // But we can try to hit a model and see.
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    const result = await model.generateContent("test");
    console.log("Success with gemini-1.5-flash");
  } catch (e) {
    console.error("Error:", e.message);
  }
}

list();
