const express = require('express');
const cors = require('cors');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

const port = process.env.PORT || 9001;
const apiKey = process.env.GEMINI_API_KEY;
const modelName = process.env.GEMINI_MODEL || 'gemini-2.0-flash';

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
        
        // --- LOCAL INTELLIGENCE (Fast answers for common stats) ---
        const lowerQuery = userQuery.toLowerCase();
        if (contextType === 'GLOBAL' && aggregatedData) {
            if (lowerQuery.includes('how many') && (lowerQuery.includes('company') || lowerQuery.includes('companies'))) {
                return res.json({ answer: `You have a total of ${aggregatedData.companyCount || 0} companies registered.`, confidence: 1.0, references: ["Database company count"] });
            }
            if (lowerQuery.includes('how many') && (lowerQuery.includes('vehicle') || lowerQuery.includes('car'))) {
                return res.json({ answer: `You currently have ${aggregatedData.vehicleCount || 0} vehicles in your fleet.`, confidence: 1.0, references: ["Database vehicle count"] });
            }
            if (lowerQuery.includes('revenue')) {
                return res.json({ answer: `Your total business revenue is ₹${aggregatedData.totalRevenue?.toLocaleString()}.`, confidence: 1.0, references: ["Total revenue sum"] });
            }
        }

        const model = genAI.getGenerativeModel({ model: modelName });
        
        // Construct detailed context string
        let contextInfo = "";
        if (contextType === 'BILL' && billData) {
            contextInfo = `
BILL CONTEXT:
- Bill Number: ${billData.billNumber}
- Company: ${billData.companyName}
- Distance: ${billData.totalKm} KM
- Time: ${billData.totalHours} Hours
- Charges: ${JSON.stringify(billData.charges)}
- Total Amount: ₹${billData.totalAmount}
`;
        } else if (contextType === 'GLOBAL' && aggregatedData) {
            contextInfo = `
GLOBAL CONTEXT:
- Total Revenue: ₹${aggregatedData.totalRevenue}
- Total Companies: ${aggregatedData.companyCount}
- Total Vehicles: ${aggregatedData.vehicleCount}
- Top Companies: ${JSON.stringify(aggregatedData.topCompanies)}
- Recent Bills: ${JSON.stringify(aggregatedData.recentBills)}
`;
        }

        const prompt = `You are the Sri Tulja Bhavani Travels AI Bill Assistant.
Your goal is to answer user questions about billing and business data based ONLY on the provided context.

STRICT RULES:
1. Answer ONLY from the provided context.
2. DO NOT hallucinate or make up data.
3. If the data is insufficient to answer the question, respond exactly with: "Insufficient data to answer"
4. Keep answers short and clear (max 3-4 lines).
5. No assumptions beyond what is explicitly stated in the data.
6. Do not modify or suggest modifications to the data.

CONTEXT:
${contextInfo}

USER QUERY: "${userQuery}"

OUTPUT FORMAT (STRICT JSON):
{
  "answer": "Your clear, concise answer",
  "confidence": 0.0 to 1.0,
  "references": ["briefly mention data points used, e.g., 'totalAmount', 'charge list'"]
}`;

        console.log(`[AI Assistant] Query: "${userQuery}" [Context: ${contextType}]`);
        const result = await generateWithRetry(model, prompt);
        let text = result.response.text().trim();
        
        // Clean up JSON response if AI wraps it in markdown
        if (text.startsWith('```')) {
            text = text.replace(/```json|```/g, '').trim();
        }

        try {
            const aiResponse = JSON.parse(text);
            console.log(`[AI Assistant] Response: "${aiResponse.answer.substring(0, 50)}..." [Confidence: ${aiResponse.confidence}]`);
            res.json(aiResponse);
        } catch (parseError) {
            console.error('[AI Assistant] JSON Parse Error:', text);
            res.json({ 
                answer: text, // Fallback if AI didn't return valid JSON
                confidence: 0.5,
                references: ["Raw AI response"]
            });
        }
    } catch (error) {
        console.error('[AI Assistant] Error:', error.message);
        res.status(500).json({ 
            answer: "I encountered an error while analyzing the data. Please try again.", 
            confidence: 0,
            references: ["System Error"]
        });
    }
});

// AI Suggestions & Automation Engine Endpoint
app.post('/api/ai/generate-suggestions', async (req, res) => {
    try {
        const { currentBill, historicalPatterns } = req.body;
        const model = genAI.getGenerativeModel({ model: modelName });

        const prompt = `You are the Sri Tulja Bhavani Travels Billing Specialist.
Your goal is to suggest values for a NEW bill based on HISTORICAL patterns.

CURRENT BILL DRAFT:
- Company: ${currentBill.companyName}
- Vehicle Type: ${currentBill.vehicleType}
- Distance: ${currentBill.totalKm} KM
- Time: ${currentBill.totalHours} Hours

HISTORICAL PATTERNS:
- Average Driver Bata: ₹${historicalPatterns.averageDriverBata}
- Average Toll: ₹${historicalPatterns.averageToll}
- Average Parking: ₹${historicalPatterns.averageParking}
- Common Charges: ${JSON.stringify(historicalPatterns.commonCharges)}
- Recent Similar Bills: ${JSON.stringify(historicalPatterns.recentSimilarBills)}

STRICT RULES:
1. Suggest values ONLY if confidence is high (above 0.7).
2. DO NOT hallucinate or guess if data is missing.
3. If no clear pattern exists, return an empty "suggestions" array.
4. Keep reasons extremely concise (max 10 words).
5. Output MUST be valid JSON.

OUTPUT FORMAT (STRICT JSON):
{
  "suggestions": [
    {
      "field": "driverBata | toll | parking | otherCharges",
      "suggestedValue": "numeric or text value",
      "reason": "short explanation",
      "confidence": 0.0 to 1.0
    }
  ]
}`;

        console.log(`[AI Suggestions] Analyzing patterns for ${currentBill.companyName}...`);
        const result = await generateWithRetry(model, prompt);
        let text = result.response.text().trim();
        
        if (text.startsWith('```')) {
            text = text.replace(/```json|```/g, '').trim();
        }

        res.json(JSON.parse(text));
    } catch (error) {
        console.error('[AI Suggestions] Error:', error.message);
        res.json({ suggestions: [] });
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`🚀 AI Service (Standard) running on http://localhost:${port}`);
});
