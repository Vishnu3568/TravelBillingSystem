const express = require('express');
const cors = require('cors');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

const port = process.env.PORT || 9001;
const apiKey = process.env.GEMINI_API_KEY;
const modelName = 'gemini-2.0-flash-lite'; // Reverting to confirmed working model

if (!apiKey) {
    console.error('CRITICAL: GEMINI_API_KEY is not set.');
    process.exit(1);
}

// Initialize Standard SDK with explicit v1 API
const genAI = new GoogleGenerativeAI(apiKey);

// Helper for retries with exponential backoff
async function generateWithRetry(model, prompt, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const result = await model.generateContent(prompt);
            return result;
        } catch (error) {
            const isQuotaError = error.message.includes('429') || error.message.includes('Quota');
            if (isQuotaError && i < maxRetries - 1) {
                const wait = Math.pow(2, i) * 3000;
                console.log(`[AI] Quota hit, retrying in ${wait}ms... (Attempt ${i + 1}/${maxRetries})`);
                await new Promise(r => setTimeout(r, wait));
                continue;
            }
            throw error;
        }
    }
}

// Health Check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', model: modelName });
});

// AI Insights & Analytics Endpoint
app.post('/api/ai/generate-insights', async (req, res) => {
    try {
        const { stats } = req.body;
        const model = genAI.getGenerativeModel({ model: modelName });
        
        const prompt = `Analyze this data for 'Sri Tulja Bhavani Travels' and return ONLY JSON:
{ "insights": [{"type": "INFO|WARNING|TREND", "message": "Short insight", "confidence": 0.9}] }
Data: Revenue ₹${stats.totalRevenue}, Bills ${stats.billCount}, Top Co: ${JSON.stringify(stats.companyStats?.slice(0,3))}`;

        console.log(`[AI] Generating Insights...`);
        const result = await generateWithRetry(model, prompt);
        const responseText = result.response.text();
        res.json(JSON.parse(responseText.replace(/```json|```/g, '')));
    } catch (error) {
        console.error('[AI] Insights Error:', error.message);
        // Return friendly mock insights while waiting for quota reset
        res.json({
            insights: [
                { type: "INFO", message: "Revenue is being analyzed. Check back in a minute!", confidence: 1.0 },
                { type: "TREND", message: "Top companies are loading...", confidence: 1.0 }
            ]
        });
    }
});

// AI Bill Assistant (Chat) Endpoint
app.post('/api/ai/chat-assistant', async (req, res) => {
    try {
        const { contextType, billData, aggregatedData, userQuery } = req.body;
        
        // --- LOCAL INTELLIGENCE (Fuzzy Matching for typos & variations) ---
        const lowerQuery = userQuery.toLowerCase();
        const hasHowMany = lowerQuery.includes('how many') || lowerQuery.includes('total') || lowerQuery.includes('count');
        const hasCompany = lowerQuery.includes('company') || lowerQuery.includes('companies') || lowerQuery.includes('comapnies');
        const hasVehicle = lowerQuery.includes('vehicle') || lowerQuery.includes('car') || lowerQuery.includes('fleet');
        const hasRevenue = lowerQuery.includes('revenue') || lowerQuery.includes('earn') || lowerQuery.includes('money');

        if (contextType === 'GLOBAL' && aggregatedData) {
            if (hasHowMany && hasCompany) {
                return res.json({ answer: `You have a total of ${aggregatedData.companyCount || 0} companies registered.`, confidence: 1.0 });
            }
            if (hasHowMany && hasVehicle) {
                return res.json({ answer: `You currently have ${aggregatedData.vehicleCount || 0} vehicles in your fleet.`, confidence: 1.0 });
            }
            if (hasRevenue) {
                return res.json({ answer: `Your total business revenue is ₹${aggregatedData.totalRevenue?.toLocaleString()}.`, confidence: 1.0 });
            }
        }

        const model = genAI.getGenerativeModel({ model: modelName });
        const context = contextType === 'BILL' 
            ? `Bill: ${billData.billNumber}, Company: ${billData.companyName}, Amount: ₹${billData.totalAmount}`
            : `Total Revenue: ₹${aggregatedData.totalRevenue}, Companies: ${aggregatedData.companyCount}, Vehicles: ${aggregatedData.vehicleCount}`;

        const prompt = `You are a billing assistant. Answer briefly:
Context: ${context}
Query: ${userQuery}
Return JSON: { "answer": "...", "confidence": 0.9 }`;

        console.log(`[AI Assistant] Processing: "${userQuery}"`);
        const result = await generateWithRetry(model, prompt);
        const responseText = result.response.text();
        res.json(JSON.parse(responseText.replace(/```json|```/g, '')));
    } catch (error) {
        console.error('[AI Assistant] Error:', error.message);
        res.json({ 
            answer: "I'm processing your request. Please try again in a few seconds!", 
            confidence: 0 
        });
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`🚀 AI Service (Standard) running on http://localhost:${port}`);
});
