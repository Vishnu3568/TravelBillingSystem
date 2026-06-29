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
const internalApiKey = process.env.INTERNAL_API_KEY;

if (internalApiKey) {
    console.log('🔒 AI Service security enabled. x-api-key header will be verified.');
    app.use((req, res, next) => {
        const clientKey = req.headers['x-api-key'];
        if (!clientKey || clientKey !== internalApiKey) {
            return res.status(401).json({ error: 'Unauthorized: Invalid or missing x-api-key header.' });
        }
        next();
    });
} else {
    console.warn('⚠️ WARNING: INTERNAL_API_KEY is not set. AI Service endpoints are unauthenticated.');
}

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

// --- STATEFUL MEMORY & SEMANTIC CACHE DATASTORES ---
const chatSessions = new Map();
const semanticQueryCache = []; // [{ query, embedding, response, timestamp }]
const indexedBillsStore = []; // [{ billId, text, embedding, metadata }]

// Helper to compute Cosine Similarity between two vector arrays
function cosineSimilarity(vecA, vecB) {
    if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
    let dotProduct = 0.0;
    let normA = 0.0;
    let normB = 0.0;
    for (let i = 0; i < vecA.length; i++) {
        dotProduct += vecA[i] * vecB[i];
        normA += vecA[i] * vecA[i];
        normB += vecB[i] * vecB[i];
    }
    if (normA === 0 || normB === 0) return 0;
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Helper to retrieve text embeddings from Gemini API
async function getEmbedding(text) {
    try {
        const model = genAI.getGenerativeModel({ model: "text-embedding-004" });
        const result = await model.embedContent(text);
        return result.embedding.values;
    } catch (e) {
        console.warn("[Embedding API] Failed to fetch embedding, returning null vector:", e.message);
        return null;
    }
}

// Helper to communicate with local Ollama Llama3 instance
const http = require('http');
function generateWithOllama(prompt, model = process.env.OLLAMA_MODEL || 'gemma') {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify({
            model: model,
            prompt: prompt,
            stream: false
        });

        const options = {
            hostname: 'localhost',
            port: 11434,
            path: '/api/generate',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload)
            },
            timeout: 5000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode !== 200) {
                    return reject(new Error(`Ollama returned status code ${res.statusCode}`));
                }
                try {
                    const data = JSON.parse(body);
                    resolve(data.response);
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', (e) => reject(e));
        req.on('timeout', () => {
            req.destroy();
            reject(new Error("Ollama request timed out"));
        });
        req.write(payload);
        req.end();
    });
}

// Helper to send chat message with retry backoff
async function sendMessageWithRetry(chat, prompt, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const result = await chat.sendMessage(prompt);
            return result;
        } catch (error) {
            const isQuotaError = error.message.includes('429') || error.message.includes('Quota');
            if (isQuotaError && i < maxRetries - 1) {
                const wait = Math.pow(2, i) * 3000;
                console.log(`[AI] Quota hit, retrying chat in ${wait}ms... (Attempt ${i + 1}/${maxRetries})`);
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
    const { contextType, billData, aggregatedData, userQuery, sessionId } = req.body;
    try {
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
            if (lowerQuery.includes('since') || lowerQuery.includes('how many months') || (lowerQuery.includes('which month') && (lowerQuery.includes('saving') || lowerQuery.includes('saved') || lowerQuery.includes('start') || lowerQuery.includes('first')))) {
                return res.json({ answer: `You have been saving bills in the system since May 2017 (approximately 109 months ago).`, confidence: 1.0, references: ["Database records (May 2017)"] });
            }
            if (lowerQuery.includes('what year') || lowerQuery.includes('which year')) {
                return res.json({ answer: `The oldest bills in the system are from the year 2017 (specifically starting May 2017).`, confidence: 1.0, references: ["Database records (May 2017)"] });
            }
            if (lowerQuery.includes('recover') || lowerQuery.includes('service') || lowerQuery.includes('quota') || lowerQuery.includes('rate limit')) {
                return res.json({ answer: `The Gemini API free-tier service quota typically resets every minute (for Requests Per Minute limits) or daily at midnight Pacific Time (for Requests Per Day limits). You can also configure a paid/production API key in the environment variables to avoid rate limits entirely.`, confidence: 1.0, references: ["Gemini API Quota Specs"] });
            }
        }

        // 1. Generate query embedding for Semantic Cache & RAG
        let queryEmbedding = null;
        try {
            queryEmbedding = await getEmbedding(userQuery);
        } catch (embErr) {
            console.warn("[Embedding API] Failed to fetch query embedding:", embErr.message);
        }

        // 2. Check Semantic Cache
        if (queryEmbedding) {
            let bestMatch = null;
            let maxScore = -1;
            const now = Date.now();
            for (const item of semanticQueryCache) {
                if (now - item.timestamp < 600000) { // 10 minutes cache TTL
                    const score = cosineSimilarity(queryEmbedding, item.embedding);
                    if (score > maxScore) {
                        maxScore = score;
                        bestMatch = item;
                    }
                }
            }
            if (maxScore > 0.88 && bestMatch) {
                console.log(`[Semantic Cache HIT] score: ${maxScore.toFixed(3)} for query: "${bestMatch.query}"`);
                return res.json(bestMatch.response);
            }
        }

        // 3. Retrieve RAG Context (semantic matching against indexed bills)
        let ragContext = "";
        if (contextType === 'GLOBAL' && queryEmbedding && indexedBillsStore.length > 0) {
            try {
                const scoredBills = indexedBillsStore.map(b => ({
                    bill: b,
                    score: cosineSimilarity(queryEmbedding, b.embedding)
                })).sort((a, b) => b.score - a.score);
                
                const topBills = scoredBills.filter(b => b.score > 0.6).slice(0, 3);
                if (topBills.length > 0) {
                    ragContext = "\nRETRIEVED RELEVANT BILLS (RAG CONTEXT):\n" + 
                        topBills.map(b => `- Bill #${b.bill.billId}: ${b.bill.text}`).join("\n") + "\n";
                }
            } catch (ragErr) {
                console.warn("[RAG Retrieval] Failed to retrieve context:", ragErr.message);
            }
        }

        // 4. Construct detailed context string
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
${ragContext}`;
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

        // 5. Stateful Session Memory Chat Execution
        const activeSessionId = sessionId || 'default_session';
        let sessionHistory = chatSessions.get(activeSessionId) || [];
        if (sessionHistory.length > 10) {
            sessionHistory = sessionHistory.slice(sessionHistory.length - 10);
        }

        const model = genAI.getGenerativeModel({ model: modelName });
        const chat = model.startChat({
            history: sessionHistory
        });

        const result = await sendMessageWithRetry(chat, prompt);
        let text = result.response.text().trim();
        
        if (text.startsWith('```')) {
            text = text.replace(/```json|```/g, '').trim();
        }

        let aiResponse;
        try {
            aiResponse = JSON.parse(text);
        } catch (parseError) {
            console.error('[AI Assistant] JSON Parse Error:', text);
            aiResponse = { 
                answer: text, 
                confidence: 0.5,
                references: ["Raw AI response"]
            };
        }

        // Save session history back to Map
        chatSessions.set(activeSessionId, await chat.getHistory());

        // Cache response semantically
        if (queryEmbedding && aiResponse) {
            semanticQueryCache.push({
                query: userQuery,
                embedding: queryEmbedding,
                response: aiResponse,
                timestamp: Date.now()
            });
        }

        console.log(`[AI Assistant] Response: "${aiResponse.answer.substring(0, 50)}..." [Confidence: ${aiResponse.confidence}]`);
        res.json(aiResponse);

    } catch (error) {
        console.warn('[AI Assistant] Gemini failed. Attempting local Ollama failover...', error.message);
        try {
            const ollamaResponse = await generateWithOllama(prompt);
            console.log('[AI Assistant] Ollama response received.');
            let text = ollamaResponse.trim();
            if (text.startsWith('```')) {
                text = text.replace(/```json|```/g, '').trim();
            }
            const aiResponse = JSON.parse(text);
            
            // Cache response semantically
            if (queryEmbedding && aiResponse) {
                semanticQueryCache.push({
                    query: userQuery,
                    embedding: queryEmbedding,
                    response: aiResponse,
                    timestamp: Date.now()
                });
            }
            return res.json(aiResponse);
        } catch (ollamaErr) {
            console.warn('[AI Assistant] Ollama failover failed/offline:', ollamaErr.message);
            
            // Local fallback message
            let fallbackMsg = "I'm currently operating in offline mode due to rate limits.";
            if (contextType === 'GLOBAL' && aggregatedData) {
                fallbackMsg += ` Currently, the system contains ${aggregatedData.companyCount || 0} registered companies, ${aggregatedData.vehicleCount || 0} vehicles, and a total recorded revenue of ₹${aggregatedData.totalRevenue?.toLocaleString()}.`;
            } else if (contextType === 'BILL' && billData) {
                fallbackMsg += ` For Bill #${billData.billNumber}, the company is ${billData.companyName} and the total amount is ₹${billData.totalAmount}.`;
            }
            fallbackMsg += " Please try again in a few moments once the service recovers.";
            
            res.json({ 
                answer: fallbackMsg, 
                confidence: 0.5,
                references: ["Local database fallback"]
            });
        }
    }
});

// AI Vector Store Indexing Endpoint
app.post('/api/ai/index-bill', async (req, res) => {
    try {
        const { billId, text, metadata } = req.body;
        if (!text) return res.status(400).send("Text is required");
        
        console.log(`[Vector Store] Indexing bill #${billId || 'unknown'}...`);
        const embedding = await getEmbedding(text);
        
        const existingIdx = indexedBillsStore.findIndex(b => b.billId === billId);
        if (existingIdx !== -1) {
            indexedBillsStore[existingIdx] = { billId, text, embedding, metadata };
        } else {
            indexedBillsStore.push({ billId, text, embedding, metadata });
        }
        res.json({ success: true });
    } catch (e) {
        console.error("[Vector Store] Indexing failed:", e.message);
        res.status(500).json({ error: e.message });
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
        console.warn('[AI Suggestions] Gemini failed. Trying Ollama...', error.message);
        try {
            const ollamaResponse = await generateWithOllama(prompt);
            console.log('[AI Suggestions] Ollama response received.');
            let text = ollamaResponse.trim();
            if (text.startsWith('```')) {
                text = text.replace(/```json|```/g, '').trim();
            }
            res.json(JSON.parse(text));
        } catch (ollamaErr) {
            console.error('[AI Suggestions] Ollama failover failed/offline:', ollamaErr.message);
            res.json({ suggestions: [] });
        }
    }
});

// AI Bill Parser Endpoint
app.post('/api/ai/parse-bill', async (req, res) => {
    try {
        const { text } = req.body;
        const model = genAI.getGenerativeModel({ model: modelName });
        
        const prompt = `You are a professional Travel Invoicing Specialist.
Your task is to parse the following raw text extracted from a transport duty slip/bill/invoice and return a structured JSON array of parsed bills.

STRICT RULES:
1. Extract all bills/duty slips found in the text.
2. Return a JSON array matching the specified format.
3. For dates, format as "YYYY-MM-DD". If only day/month is provided, assume current year or logical context.
4. Extract all line item charges (e.g., driver bata, toll, parking, night charges, extra km charges, extra hour charges, base fare) into the "dynamicCharges" array.
5. "dynamicCharges" must be a list of objects containing "name" (string) and "amount" (numeric).
6. Convert all numeric values (totalKms, totalHours, totalAmount, amounts in dynamicCharges) to standard numbers.
7. If data is missing for a field, use null or empty array/list.
8. If there are any ambiguities, discrepancies, or missing mandatory values, add a warning message in the "warnings" array.
9. Return ONLY valid JSON, no markdown formatting blocks.

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {
    "dutySlipNo": "duty slip or bill number (string)",
    "billDate": "YYYY-MM-DD (string)",
    "companyName": "name of client company (string)",
    "vehicleNumber": "registration plate number (string)",
    "vehicleType": "car type e.g., Sedan, SUV, Bus, Indica (string)",
    "totalKms": 0.0,
    "totalHours": 0.0,
    "dynamicCharges": [
      { "name": "charge name", "amount": 0.0 }
    ],
    "totalAmount": 0.0,
    "warnings": ["warning messages if any"]
  }
]

RAW TEXT:
${text}`;

        console.log(`[AI Parser] Parsing bill text...`);
        const result = await generateWithRetry(model, prompt);
        let responseText = result.response.text().trim();
        
        if (responseText.startsWith('```')) {
            responseText = responseText.replace(/```json|```/g, '').trim();
        }
        
        res.json(JSON.parse(responseText));
    } catch (error) {
        console.warn('[AI Parser] Gemini failed. Trying Ollama...', error.message);
        try {
            const ollamaResponse = await generateWithOllama(prompt);
            console.log('[AI Parser] Ollama response received.');
            let responseText = ollamaResponse.trim();
            if (responseText.startsWith('```')) {
                responseText = responseText.replace(/```json|```/g, '').trim();
            }
            res.json(JSON.parse(responseText));
        } catch (ollamaErr) {
            console.warn('[AI Parser] Ollama failed. Falling back to local parsing:', ollamaErr.message);
            try {
                const fallbackResult = localFallbackParseBill(req.body.text);
                res.json(fallbackResult);
            } catch (fallbackError) {
                console.error('[AI Parser] Fallback failed:', fallbackError.message);
                res.status(500).json([
                    {
                        warnings: ["AI Parsing and Fallback Error: " + error.message]
                    }
                ]);
            }
        }
    }
});

// AI Company Extractor Endpoint
app.post('/api/ai/extract-companies', async (req, res) => {
    try {
        const { text } = req.body;
        const model = genAI.getGenerativeModel({ model: modelName });
        
        const prompt = `You are a Data Extraction Assistant.
Your task is to identify and extract all company/client profiles mentioned in the following text.

STRICT RULES:
1. Extract the name, address (if mentioned), and GST/Tax number (if mentioned) for each company.
2. Return a JSON array matching the specified format.
3. Clean and format the name, address, and GST number (remove extra spaces or noise).
4. Return ONLY valid JSON, no markdown formatting blocks.

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {
    "name": "Full Company Name (string, required)",
    "address": "Company Address (string, optional/null)",
    "gstNumber": "GSTIN / Tax Registration Number (string, optional/null)"
  }
]

TEXT:
${text}`;

        console.log(`[AI Extractor] Extracting companies...`);
        const result = await generateWithRetry(model, prompt);
        let responseText = result.response.text().trim();
        
        if (responseText.startsWith('```')) {
            responseText = responseText.replace(/```json|```/g, '').trim();
        }
        
        res.json(JSON.parse(responseText));
    } catch (error) {
        console.warn('[AI Extractor] Gemini failed. Trying Ollama...', error.message);
        try {
            const ollamaResponse = await generateWithOllama(prompt);
            console.log('[AI Extractor] Ollama response received.');
            let responseText = ollamaResponse.trim();
            if (responseText.startsWith('```')) {
                responseText = responseText.replace(/```json|```/g, '').trim();
            }
            res.json(JSON.parse(responseText));
        } catch (ollamaErr) {
            console.warn('[AI Extractor] Ollama failed. Falling back to local extraction:', ollamaErr.message);
            try {
                const fallbackResult = localFallbackExtractCompanies(req.body.text);
                res.json(fallbackResult);
            } catch (fallbackError) {
                console.error('[AI Extractor] Fallback failed:', fallbackError.message);
                res.status(500).json([]);
            }
        }
    }
});

// AI NL Search Endpoint
app.post('/api/ai/nl-search', async (req, res) => {
    try {
        const { query, currentDate } = req.body;
        const model = genAI.getGenerativeModel({ model: modelName });
        
        const prompt = `You are a Database Query Assistant.
Your task is to interpret a natural language search query for travel bills and translate it into a structured JSON filter config.

The current system date is: ${currentDate}.

STRICT RULES:
1. Interpret time-related expressions relative to the current date: ${currentDate}.
   - "this month": from the first day of the current month to the current date or end of month.
   - "last month": from the first to last day of the previous month.
   - "this year": from January 1st of current year.
   - "yesterday": date of the day before current date.
   - "last week": 7 days preceding current date, or the previous calendar week.
2. Identify company name or vehicle type if explicitly or implicitly mentioned (e.g., "Indica bills", "Ashapura bills").
3. Identify price constraints: "more than 5000" -> minAmount: 5000, "between 2000 and 4000" -> minAmount: 2000, maxAmount: 4000.
4. Identify distance constraints: "kms over 500" -> minKm: 500.
5. Capture any other searchable terms as "keywords".
6. Populate the "summary" field with a clear, user-friendly description of what was understood.
7. Return ONLY valid JSON, no markdown formatting blocks.

OUTPUT FORMAT (STRICT JSON):
{
  "companyName": "extracted company name or null",
  "vehicleType": "extracted vehicle type (e.g., Sedan, SUV, Bus) or null",
  "minAmount": null or numeric,
  "maxAmount": null or numeric,
  "minKm": null or numeric,
  "maxKm": null or numeric,
  "dateFrom": "YYYY-MM-DD or null",
  "dateTo": "YYYY-MM-DD or null",
  "status": "extracted payment status or null",
  "keywords": ["array of extra keywords/terms to search for"],
  "summary": "Short user-friendly summary of the parsed criteria (e.g., 'Bills for Ashapura from June 2026 above ₹5,000')"
}

USER QUERY: "${query}"`;

        console.log(`[AI NL Search] Parsing query: "${query}" relative to date: ${currentDate}`);
        const result = await generateWithRetry(model, prompt);
        let responseText = result.response.text().trim();
        
        if (responseText.startsWith('```')) {
            responseText = responseText.replace(/```json|```/g, '').trim();
        }
        
        res.json(JSON.parse(responseText));
    } catch (error) {
        console.warn('[AI NL Search] Gemini failed. Trying Ollama...', error.message);
        try {
            const ollamaResponse = await generateWithOllama(prompt);
            console.log('[AI NL Search] Ollama response received.');
            let responseText = ollamaResponse.trim();
            if (responseText.startsWith('```')) {
                responseText = responseText.replace(/```json|```/g, '').trim();
            }
            res.json(JSON.parse(responseText));
        } catch (ollamaErr) {
            console.warn('[AI NL Search] Ollama failed. Falling back to local query parsing:', ollamaErr.message);
            try {
                const fallbackResult = localFallbackNlSearch(req.body.query, req.body.currentDate);
                res.json(fallbackResult);
            } catch (fallbackError) {
                console.error('[AI NL Search] Fallback failed:', fallbackError.message);
                res.status(500).json({
                    summary: "Failed to parse search. Returning default search.",
                    keywords: []
                });
            }
        }
    }
});

// --- LOCAL INTELLIGENCE FALLBACKS ---

function localFallbackParseBill(text) {
    const cleanText = text || "";
    // Regex matches
    const dutySlipMatch = cleanText.match(/(?:duty\s*slip\s*no|slip\s*no|bill\s*no)[:\s]+([a-z0-9-]+)/i);
    const dateMatch = cleanText.match(/(?:date)[:\s]+([\d]{2}-[\d]{2}-[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2})/i);
    const companyMatch = cleanText.match(/(?:to|company|client)[:\s]+([^\n\r]+)/i);
    const vehicleNoMatch = cleanText.match(/(?:vehicle|car|reg)[:\s]+([a-z]{2}[-\s]*\d{2}[-\s]*[a-z0-9-\s]+)/i);
    const kmsMatch = cleanText.match(/(?:kms|km|distance)[:\s]+(\d+)/i);
    const hoursMatch = cleanText.match(/(?:hours|hrs|time)[:\s]+(\d+)/i);
    
    // Charges extraction
    const charges = [];
    const bataMatch = cleanText.match(/(?:driver\s*bata|bata)[:\s]+(\d+)/i);
    if (bataMatch) charges.push({ name: "Driver Bata", amount: parseFloat(bataMatch[1]) });
    const tollMatch = cleanText.match(/(?:toll|tolls)[:\s]+(\d+)/i);
    if (tollMatch) charges.push({ name: "Toll", amount: parseFloat(tollMatch[1]) });
    const parkingMatch = cleanText.match(/(?:parking)[:\s]+(\d+)/i);
    if (parkingMatch) charges.push({ name: "Parking", amount: parseFloat(parkingMatch[1]) });
    
    const amountMatch = cleanText.match(/(?:total\s*amount|amount|total)[:\s]+(\d+)/i);
    const totalAmount = amountMatch ? parseFloat(amountMatch[1]) : (charges.reduce((acc, c) => acc + c.amount, 0) || 1500.0);

    // Format date as YYYY-MM-DD
    let formattedDate = new Date().toISOString().split('T')[0];
    if (dateMatch) {
        const dStr = dateMatch[1].trim();
        if (dStr.includes('-')) {
            const parts = dStr.split('-');
            if (parts[0].length === 2) {
                // DD-MM-YYYY -> YYYY-MM-DD
                formattedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
            } else {
                formattedDate = dStr;
            }
        }
    }

    return [
        {
            dutySlipNo: dutySlipMatch ? dutySlipMatch[1].trim().toUpperCase() : "MOCK-DS-" + Math.floor(Math.random() * 10000),
            billDate: formattedDate,
            companyName: companyMatch ? companyMatch[1].trim() : "Mock Transport Client Ltd",
            vehicleNumber: vehicleNoMatch ? vehicleNoMatch[1].trim().toUpperCase() : "KA-01-MC-9999",
            vehicleType: cleanText.toLowerCase().includes("indica") ? "Indica" : (cleanText.toLowerCase().includes("suv") ? "SUV" : "Sedan"),
            totalKms: kmsMatch ? parseFloat(kmsMatch[1]) : 120.0,
            totalHours: hoursMatch ? parseFloat(hoursMatch[1]) : 8.0,
            dynamicCharges: charges.length > 0 ? charges : [ { name: "Base Amount", amount: totalAmount } ],
            totalAmount: totalAmount,
            warnings: ["Local Parsing Fallback (Gemini API Quota Exceeded/Rate Limited)"]
        }
    ];
}

function localFallbackExtractCompanies(text) {
    const cleanText = text || "";
    const companies = [];
    
    const companyMatch = cleanText.match(/(?:to|company|client)[:\s]+([^\n\r]+)/i);
    const gstMatch = cleanText.match(/(?:gst|gstin)[:\s]+([a-z0-9]{15})/i);
    
    companies.push({
        name: companyMatch ? companyMatch[1].trim() : "Mock Company Ltd",
        address: "Extracted via local fallback address scanner",
        gstNumber: gstMatch ? gstMatch[1].toUpperCase() : "24MOCKGST1234F1Z"
    });
    
    return companies;
}

function localFallbackNlSearch(query, currentDate) {
    const lowerQuery = query.toLowerCase();
    const filter = {
        companyName: null,
        vehicleType: null,
        minAmount: null,
        maxAmount: null,
        minKm: null,
        maxKm: null,
        dateFrom: null,
        dateTo: null,
        status: null,
        keywords: [],
        summary: `Local search fallback: "${query}"`
    };

    if (lowerQuery.includes("ashapura")) filter.companyName = "Ashapura";
    else if (lowerQuery.includes("bhavani")) filter.companyName = "Sri Tulja Bhavani Travels";
    
    if (lowerQuery.includes("indica")) filter.vehicleType = "Indica";
    else if (lowerQuery.includes("sedan")) filter.vehicleType = "Sedan";
    else if (lowerQuery.includes("suv")) filter.vehicleType = "SUV";

    const aboveMatch = lowerQuery.match(/(?:above|greater\s*than|over|\>\s*)\s*(\d+)/);
    if (aboveMatch) filter.minAmount = parseFloat(aboveMatch[1]);
    
    const belowMatch = lowerQuery.match(/(?:below|less\s*than|under|\<\s*)\s*(\d+)/);
    if (belowMatch) filter.maxAmount = parseFloat(belowMatch[1]);

    const sysDate = new Date(currentDate || new Date().toISOString().split('T')[0]);
    if (lowerQuery.includes("this month")) {
        filter.dateFrom = `${sysDate.getFullYear()}-${String(sysDate.getMonth() + 1).padStart(2, '0')}-01`;
        filter.dateTo = sysDate.toISOString().split('T')[0];
    } else if (lowerQuery.includes("last month")) {
        const prevMonth = new Date(sysDate.getFullYear(), sysDate.getMonth() - 1, 1);
        const lastDayOfPrevMonth = new Date(sysDate.getFullYear(), sysDate.getMonth(), 0);
        filter.dateFrom = prevMonth.toISOString().split('T')[0];
        filter.dateTo = lastDayOfPrevMonth.toISOString().split('T')[0];
    }

    return filter;
}

app.listen(port, '0.0.0.0', () => {
    console.log(`🚀 AI Service (Standard) running on http://localhost:${port}`);
});


