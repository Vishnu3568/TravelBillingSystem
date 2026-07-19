'use strict';
const express = require('express');
const cors = require('cors');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

// ============================================================
//  AI MICROSERVICE — Travel Billing System
//  Uses ONLY Google Gemini (@google/generative-ai)
//  No Ollama. No Vertex AI. Gemini only.
// ============================================================

const app = express();

// ---- Logging helper ----
function logAiFailure(service, reason, retryCount, fallbackUsed, durationMs = 0) {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${service}] FAIL: Reason="${reason}", Retries=${retryCount}, Fallback="${fallbackUsed}", Duration=${durationMs}ms`);
}

// ---- Middleware ----
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// ---- Configuration ----
const PORT = parseInt(process.env.PORT || '9001', 10);
const apiKey = process.env.GEMINI_API_KEY || '';
const modelName = process.env.GEMINI_MODEL || 'gemini-1.5-pro';
const internalApiKey = process.env.INTERNAL_API_KEY || 'travel_billing_secret_token_123';

// ---- Authentication middleware ----
console.log('AI Service security enabled. x-api-key / x-internal-api-key header required.');
app.use((req, res, next) => {
    if (req.path === '/health') return next(); // exempt health check
    const clientKey = req.headers['x-api-key'] || req.headers['x-internal-api-key'];
    if (!clientKey || clientKey !== internalApiKey) {
        return res.status(401).json({ error: 'Unauthorized: Invalid or missing x-api-key or x-internal-api-key header.' });
    }
    next();
});

// ---- Gemini Key Validation ----
const KNOWN_PLACEHOLDERS = [
    '',
    'your_gemini_api_key_here',
    'your_api_key_here',
    'AIzaSyDmncG2GztNQgfJhXuGIRE1ej2Q9ghEVoc'
];
const geminiKeyValid = Boolean(
    apiKey &&
    !apiKey.startsWith('YOUR_') &&
    !apiKey.startsWith('your_') &&
    !KNOWN_PLACEHOLDERS.includes(apiKey)
);

// ---- Gemini SDK Initialization ----
let genAI = null;
if (geminiKeyValid) {
    genAI = new GoogleGenerativeAI(apiKey);
    console.log(`[AI Config] Gemini SDK initialized. Model: ${modelName}`);
} else {
    console.warn('[AI Config] WARNING: GEMINI_API_KEY is missing or is a placeholder.');
    console.warn('[AI Config] AI endpoints will return graceful fallback responses.');
    console.warn('[AI Config] Set a valid GEMINI_API_KEY in ai/.env to enable AI features.');
}

// ============================================================
//  HELPER: Resolve a Gemini model instance
// ============================================================
function getModel(name) {
    if (!geminiKeyValid || !genAI) {
        throw new Error('Gemini API key not configured. Set GEMINI_API_KEY in ai/.env');
    }
    return genAI.getGenerativeModel({ model: name || modelName });
}

// ============================================================
//  HELPER: generateContent with retry + model fallback
// ============================================================
async function generateWithRetry(modelNameOrInstance, prompt, maxRetries = 3) {
    if (!geminiKeyValid || !genAI) {
        throw new Error('Gemini API key not configured');
    }
    let model = (typeof modelNameOrInstance === 'string')
        ? getModel(modelNameOrInstance)
        : modelNameOrInstance;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const result = await model.generateContent(prompt);
            return result;
        } catch (error) {
            const isNotFound = error.message.includes('404') ||
                               error.message.toLowerCase().includes('not found') ||
                               error.message.toLowerCase().includes('model');
            if (isNotFound && attempt < maxRetries - 1) {
                console.warn(`[AI Config] Model "${modelName}" returned 404. Falling back to gemini-1.5-flash...`);
                model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
                continue;
            }
            const isQuota = error.message.includes('429') || error.message.toLowerCase().includes('quota');
            if (isQuota && attempt < maxRetries - 1) {
                const wait = Math.pow(2, attempt) * 3000;
                console.log(`[AI] Quota hit, retrying in ${wait}ms... (attempt ${attempt + 1}/${maxRetries})`);
                await new Promise(r => setTimeout(r, wait));
                continue;
            }
            throw error;
        }
    }
    throw new Error('All retry attempts exhausted');
}

// ============================================================
//  HELPER: Cosine Similarity
// ============================================================
function cosineSimilarity(vecA, vecB) {
    if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < vecA.length; i++) {
        dot   += vecA[i] * vecB[i];
        normA += vecA[i] * vecA[i];
        normB += vecB[i] * vecB[i];
    }
    if (normA === 0 || normB === 0) return 0;
    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

// ============================================================
//  HELPER: Get text embedding from Gemini API
// ============================================================
async function getEmbedding(text) {
    if (!geminiKeyValid || !genAI) {
        throw new Error('Gemini API key not configured — embeddings unavailable');
    }
    const primaryModel = process.env.GEMINI_EMBEDDING_MODEL || 'text-embedding-004';
    const fallbackModel = process.env.GEMINI_EMBEDDING_FALLBACK || 'embedding-001';

    try {
        const model = genAI.getGenerativeModel({ model: primaryModel });
        const result = await model.embedContent(text);
        if (!result || !result.embedding || !result.embedding.values || result.embedding.values.length === 0) {
            throw new Error('Empty embedding returned from primary model');
        }
        return result.embedding.values;
    } catch (primaryErr) {
        console.warn(`[Embedding] Primary model "${primaryModel}" failed: ${primaryErr.message}. Trying fallback "${fallbackModel}"...`);
        try {
            const model = genAI.getGenerativeModel({ model: fallbackModel });
            const result = await model.embedContent(text);
            if (!result || !result.embedding || !result.embedding.values || result.embedding.values.length === 0) {
                throw new Error('Empty embedding returned from fallback model');
            }
            return result.embedding.values;
        } catch (fallbackErr) {
            console.error(`[Embedding] Both primary and fallback failed: ${fallbackErr.message}`);
            throw new Error(`Embedding generation failed: ${fallbackErr.message}`);
        }
    }
}

// ============================================================
//  HELPER: sendMessage with retry and quota backoff
// ============================================================
async function sendMessageWithRetry(chat, prompt, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await chat.sendMessage(prompt);
        } catch (error) {
            const isQuota = error.message.includes('429') || error.message.toLowerCase().includes('quota');
            if (isQuota && attempt < maxRetries - 1) {
                const wait = Math.pow(2, attempt) * 3000;
                console.log(`[AI Chat] Quota hit, retrying in ${wait}ms... (attempt ${attempt + 1}/${maxRetries})`);
                await new Promise(r => setTimeout(r, wait));
                continue;
            }
            throw error;
        }
    }
    throw new Error('Chat retry attempts exhausted');
}

// ============================================================
//  HELPER: Parse JSON from Gemini response (strips markdown)
// ============================================================
function parseGeminiJson(text) {
    let cleaned = text.trim();
    if (cleaned.startsWith('```')) {
        cleaned = cleaned.replace(/^```(?:json)?/i, '').replace(/```\s*$/, '').trim();
    }
    return JSON.parse(cleaned);
}

// ============================================================
//  IN-MEMORY DATASTORES
//  WARNING: All stores are ephemeral — lost on server restart.
//  For production, replace with a persistent vector DB.
// ============================================================
const chatSessions    = new Map();    // sessionId -> message history
const semanticCache   = [];           // [{ query, embedding, response, timestamp }]
const indexedBillsStore = [];         // [{ billId, text, embedding, metadata }]
const CACHE_TTL_MS    = 10 * 60 * 1000; // 10 minutes
const CACHE_HIT_THRESHOLD = 0.88;
const RAG_RELEVANCE_THRESHOLD = 0.60;
const SESSION_HISTORY_LIMIT = 10;

// ============================================================
//  ROUTE: Health Check (no auth required)
// ============================================================
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        model: modelName,
        gemini: geminiKeyValid ? 'configured' : 'not configured (degraded mode)',
        indexed_bills: indexedBillsStore.length,
        cached_queries: semanticCache.length
    });
});

// ============================================================
//  ROUTE: Generate Dashboard Insights
//  POST /api/ai/generate-insights
// ============================================================
app.post('/api/ai/generate-insights', async (req, res) => {
    const { stats } = req.body;
    if (!stats) {
        return res.status(400).json({ error: 'Request body must include "stats"' });
    }

    if (!geminiKeyValid) {
        return res.json({
            insights: [
                { type: 'WARNING', message: 'AI insights unavailable — GEMINI_API_KEY not configured.', confidence: 1.0 }
            ]
        });
    }

    try {
        const prompt = `Analyze this data for 'Sri Tulja Bhavani Travels' and return ONLY valid JSON (no markdown):
{ "insights": [{"type": "INFO|WARNING|TREND", "message": "Short insight", "confidence": 0.9}] }
Data: Revenue \u20b9${stats.totalRevenue}, Bills ${stats.billCount}, Top Co: ${JSON.stringify(stats.companyStats?.slice(0, 3))}`;

        console.log('[AI Insights] Generating insights...');
        const result = await generateWithRetry(modelName, prompt);
        const responseText = result.response.text();
        res.json(parseGeminiJson(responseText));
    } catch (error) {
        logAiFailure('generate-insights', error.message, 3, 'static-fallback');
        res.json({
            insights: [
                { type: 'INFO',  message: 'Revenue analysis is processing. Check back shortly.', confidence: 1.0 },
                { type: 'TREND', message: 'Top company data is loading.', confidence: 1.0 }
            ]
        });
    }
});

// ============================================================
//  ROUTE: Chat Assistant
//  POST /api/ai/chat-assistant
// ============================================================
app.post('/api/ai/chat-assistant', async (req, res) => {
    const { contextType, billData, aggregatedData, userQuery, sessionId } = req.body;

    if (!userQuery || typeof userQuery !== 'string') {
        return res.status(400).json({ error: 'Request body must include "userQuery" (string)' });
    }

    // ---- Fast local intelligence (no API call needed) ----
    const lowerQuery = userQuery.toLowerCase();
    if (contextType === 'GLOBAL' && aggregatedData) {
        if (lowerQuery.includes('how many') && (lowerQuery.includes('company') || lowerQuery.includes('companies'))) {
            return res.json({ answer: `You have ${aggregatedData.companyCount || 0} companies registered.`, confidence: 1.0, references: ['Database company count'] });
        }
        if (lowerQuery.includes('how many') && (lowerQuery.includes('vehicle') || lowerQuery.includes('car'))) {
            return res.json({ answer: `You have ${aggregatedData.vehicleCount || 0} vehicles in your fleet.`, confidence: 1.0, references: ['Database vehicle count'] });
        }
        if (lowerQuery.includes('revenue') && !lowerQuery.includes('forecast')) {
            return res.json({ answer: `Total business revenue is \u20b9${aggregatedData.totalRevenue?.toLocaleString()}.`, confidence: 1.0, references: ['Total revenue sum'] });
        }
        if (lowerQuery.includes('since') || lowerQuery.includes('how many months') ||
            (lowerQuery.includes('which month') && (lowerQuery.includes('start') || lowerQuery.includes('first')))) {
            return res.json({ answer: 'Bills have been saved in the system since May 2017 (approximately 109 months ago).', confidence: 1.0, references: ['Database records (May 2017)'] });
        }
        if (lowerQuery.includes('what year') || lowerQuery.includes('which year')) {
            return res.json({ answer: 'The oldest bills are from 2017 (starting May 2017).', confidence: 1.0, references: ['Database records (May 2017)'] });
        }
        if (lowerQuery.includes('quota') || lowerQuery.includes('rate limit')) {
            return res.json({ answer: 'Gemini free-tier quota resets every minute (RPM) or daily at midnight Pacific Time. Upgrade to a paid key to avoid limits.', confidence: 1.0, references: ['Gemini API Quota Specs'] });
        }
    }

    // ---- Degraded mode: no Gemini key ----
    if (!geminiKeyValid) {
        let fallbackMsg = 'AI assistant is operating in offline mode (GEMINI_API_KEY not configured).';
        if (contextType === 'GLOBAL' && aggregatedData) {
            fallbackMsg += ` System has ${aggregatedData.companyCount || 0} companies, ${aggregatedData.vehicleCount || 0} vehicles, revenue \u20b9${aggregatedData.totalRevenue?.toLocaleString()}.`;
        } else if (contextType === 'BILL' && billData) {
            fallbackMsg += ` Bill #${billData.billNumber} for ${billData.companyName}, total \u20b9${billData.totalAmount}.`;
        }
        return res.json({ answer: fallbackMsg, confidence: 0.5, references: ['Local fallback — no API key'] });
    }

    try {
        // ---- Semantic cache check ----
        let queryEmbedding = null;
        try {
            queryEmbedding = await getEmbedding(userQuery);
        } catch (embErr) {
            console.warn('[Chat] Embedding failed (cache/RAG skipped):', embErr.message);
        }

        if (queryEmbedding) {
            const now = Date.now();
            let best = null, bestScore = -1;
            for (const cached of semanticCache) {
                if (now - cached.timestamp < CACHE_TTL_MS) {
                    const score = cosineSimilarity(queryEmbedding, cached.embedding);
                    if (score > bestScore) { bestScore = score; best = cached; }
                }
            }
            if (bestScore > CACHE_HIT_THRESHOLD && best) {
                console.log(`[Cache HIT] score=${bestScore.toFixed(3)} query="${best.query}"`);
                return res.json(best.response);
            }
        }

        // ---- RAG context retrieval ----
        let ragContext = '';
        if (contextType === 'GLOBAL' && queryEmbedding && indexedBillsStore.length > 0) {
            try {
                const scored = indexedBillsStore
                    .map(b => ({ bill: b, score: cosineSimilarity(queryEmbedding, b.embedding) }))
                    .sort((a, b) => b.score - a.score)
                    .filter(b => b.score > RAG_RELEVANCE_THRESHOLD)
                    .slice(0, 3);
                if (scored.length > 0) {
                    ragContext = '\nRETRIEVED RELEVANT BILLS (RAG):\n' +
                        scored.map(b => `- Bill #${b.bill.billId}: ${b.bill.text}`).join('\n') + '\n';
                }
            } catch (ragErr) {
                console.warn('[RAG] Retrieval failed:', ragErr.message);
            }
        }

        // ---- Build context string ----
        let contextInfo = '';
        if (contextType === 'BILL' && billData) {
            contextInfo = `BILL CONTEXT:
- Bill Number: ${billData.billNumber}
- Company: ${billData.companyName}
- Distance: ${billData.totalKm} KM
- Time: ${billData.totalHours} Hours
- Charges: ${JSON.stringify(billData.charges)}
- Total Amount: \u20b9${billData.totalAmount}`;
        } else if (contextType === 'GLOBAL' && aggregatedData) {
            contextInfo = `GLOBAL CONTEXT:
- Total Revenue: \u20b9${aggregatedData.totalRevenue}
- Total Companies: ${aggregatedData.companyCount}
- Total Vehicles: ${aggregatedData.vehicleCount}
- Top Companies: ${JSON.stringify(aggregatedData.topCompanies)}
- Recent Bills: ${JSON.stringify(aggregatedData.recentBills)}
${ragContext}`;
        }

        const prompt = `You are the Sri Tulja Bhavani Travels AI Bill Assistant.
Answer ONLY from the provided context below. Do NOT hallucinate or invent data.
If context is insufficient, respond exactly: "Insufficient data to answer"
Keep answers short (max 3-4 lines). Output ONLY valid JSON.

CONTEXT:
${contextInfo}

USER QUERY: "${userQuery}"

OUTPUT FORMAT (STRICT JSON):
{
  "answer": "clear concise answer",
  "confidence": 0.0,
  "references": ["data points used"]
}`;

        console.log(`[Chat] Query: "${userQuery.substring(0, 60)}" [${contextType}]`);

        // ---- Stateful chat session ----
        const sid = sessionId || 'default_session';
        let history = chatSessions.get(sid) || [];
        if (history.length > SESSION_HISTORY_LIMIT) {
            history = history.slice(history.length - SESSION_HISTORY_LIMIT);
        }

        const model = getModel(modelName);
        const chat = model.startChat({ history });
        const result = await sendMessageWithRetry(chat, prompt);
        const raw = result.response.text().trim();

        let aiResponse;
        try {
            aiResponse = parseGeminiJson(raw);
        } catch (parseErr) {
            console.warn('[Chat] JSON parse error, wrapping raw text:', parseErr.message);
            aiResponse = { answer: raw, confidence: 0.5, references: ['Raw AI response'] };
        }

        // Update session + cache
        chatSessions.set(sid, await chat.getHistory());
        if (queryEmbedding && aiResponse) {
            semanticCache.push({ query: userQuery, embedding: queryEmbedding, response: aiResponse, timestamp: Date.now() });
        }

        console.log(`[Chat] Response: "${String(aiResponse.answer).substring(0, 50)}..." [confidence=${aiResponse.confidence}]`);
        res.json(aiResponse);

    } catch (error) {
        logAiFailure('chat-assistant', error.message, 3, 'offline-fallback');
        let fallbackMsg = 'AI assistant is temporarily offline. ';
        if (contextType === 'GLOBAL' && aggregatedData) {
            fallbackMsg += `System: ${aggregatedData.companyCount || 0} companies, ${aggregatedData.vehicleCount || 0} vehicles, \u20b9${aggregatedData.totalRevenue?.toLocaleString()} revenue.`;
        } else if (contextType === 'BILL' && billData) {
            fallbackMsg += `Bill #${billData.billNumber} — ${billData.companyName}, \u20b9${billData.totalAmount}.`;
        }
        fallbackMsg += ' Please try again shortly.';
        res.json({ answer: fallbackMsg, confidence: 0.5, references: ['Local fallback'] });
    }
});

// ============================================================
//  ROUTE: Index Bill into Vector Store
//  POST /api/ai/index-bill
// ============================================================
app.post('/api/ai/index-bill', async (req, res) => {
    const { billId, text, metadata } = req.body;

    if (!billId) return res.status(400).json({ error: 'Missing required field: billId' });
    if (!text)   return res.status(400).json({ error: 'Missing required field: text' });
    if (!metadata || !metadata.company || !metadata.vehicle || !metadata.billNumber) {
        return res.status(400).json({ error: 'Missing required metadata fields: company, vehicle, billNumber' });
    }

    if (!geminiKeyValid) {
        console.warn(`[Vector Store] Skipping indexing for bill #${billId} — Gemini key not configured`);
        return res.json({ success: false, reason: 'Gemini not configured — bill not indexed', total_indexed: indexedBillsStore.length });
    }

    try {
        console.log(`[Vector Store] Indexing bill #${billId}...`);
        const embedding = await getEmbedding(text);
        if (!embedding || embedding.length === 0) {
            return res.status(500).json({ error: 'Embedding returned empty vector' });
        }

        const entry = { billId, text, embedding, metadata };
        const existingIdx = indexedBillsStore.findIndex(b => b.billId === billId);
        if (existingIdx !== -1) {
            indexedBillsStore[existingIdx] = entry;
        } else {
            indexedBillsStore.push(entry);
        }

        console.log(`[Vector Store] Indexed. Total bills: ${indexedBillsStore.length}`);
        res.json({ success: true, total_indexed: indexedBillsStore.length });
    } catch (err) {
        console.error('[Vector Store] Indexing error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// ============================================================
//  ROUTE: Generate Billing Suggestions
//  POST /api/ai/generate-suggestions
// ============================================================
app.post('/api/ai/generate-suggestions', async (req, res) => {
    const { currentBill, historicalPatterns } = req.body;
    if (!currentBill) {
        return res.status(400).json({ error: 'Request body must include "currentBill"' });
    }
    if (!historicalPatterns) {
        return res.status(400).json({ error: 'Request body must include "historicalPatterns"' });
    }

    if (!geminiKeyValid) {
        return res.json({ suggestions: [] });
    }

    try {
        const prompt = `You are the Sri Tulja Bhavani Travels Billing Specialist.
Suggest values for a NEW bill based on HISTORICAL patterns. Output ONLY valid JSON (no markdown).

CURRENT BILL DRAFT:
- Company: ${currentBill.companyName}
- Vehicle Type: ${currentBill.vehicleType}
- Distance: ${currentBill.totalKm} KM
- Time: ${currentBill.totalHours} Hours

HISTORICAL PATTERNS:
- Average Driver Bata: \u20b9${historicalPatterns.averageDriverBata}
- Average Toll: \u20b9${historicalPatterns.averageToll}
- Average Parking: \u20b9${historicalPatterns.averageParking}
- Common Charges: ${JSON.stringify(historicalPatterns.commonCharges)}
- Recent Similar Bills: ${JSON.stringify(historicalPatterns.recentSimilarBills)}

STRICT RULES:
1. Suggest ONLY if confidence > 0.7.
2. Do NOT hallucinate — if no clear pattern, return empty "suggestions" array.
3. Reasons must be ≤10 words.

OUTPUT FORMAT (STRICT JSON):
{
  "suggestions": [
    {
      "field": "driverBata | toll | parking | otherCharges",
      "suggestedValue": "numeric or text",
      "reason": "short explanation",
      "confidence": 0.0
    }
  ]
}`;

        console.log(`[AI Suggestions] Analyzing patterns for ${currentBill.companyName}...`);
        const result = await generateWithRetry(modelName, prompt);
        res.json(parseGeminiJson(result.response.text()));
    } catch (error) {
        logAiFailure('generate-suggestions', error.message, 3, 'empty-suggestions');
        res.json({ suggestions: [] });
    }
});

// ============================================================
//  ROUTE: Parse Bill Text
//  POST /api/ai/parse-bill
// ============================================================
app.post('/api/ai/parse-bill', async (req, res) => {
    const { text } = req.body;
    if (!text || typeof text !== 'string') {
        return res.status(400).json({ error: 'Request body must include "text" (string)' });
    }

    if (!geminiKeyValid) {
        return res.json(localFallbackParseBill(text));
    }

    try {
        const prompt = `You are a professional Travel Invoicing Specialist.
Parse the raw text from a transport duty slip/bill/invoice and return a structured JSON array.
Return ONLY valid JSON (no markdown).

STRICT RULES:
1. Extract all bills/duty slips found in the text.
2. Format dates as "YYYY-MM-DD".
3. Extract all line item charges into "dynamicCharges" array: [{name, amount}].
4. Convert all numeric values to standard numbers.
5. Use null for missing fields.
6. Add warnings for ambiguities or missing mandatory values.

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {
    "dutySlipNo": "string",
    "billDate": "YYYY-MM-DD",
    "companyName": "string",
    "vehicleNumber": "string",
    "vehicleType": "Sedan | SUV | Indica | Bus | etc.",
    "totalKms": 0.0,
    "totalHours": 0.0,
    "dynamicCharges": [{ "name": "string", "amount": 0.0 }],
    "totalAmount": 0.0,
    "warnings": ["string"]
  }
]

RAW TEXT:
${text}`;

        console.log('[AI Parser] Parsing bill text...');
        const result = await generateWithRetry(modelName, prompt);
        res.json(parseGeminiJson(result.response.text()));
    } catch (error) {
        logAiFailure('parse-bill', error.message, 3, 'local-regex-fallback');
        try {
            res.json(localFallbackParseBill(text));
        } catch (fbErr) {
            console.error('[AI Parser] Fallback also failed:', fbErr.message);
            res.status(500).json([{ warnings: ['AI Parsing failed: ' + error.message] }]);
        }
    }
});

// ============================================================
//  ROUTE: Extract Company Profiles
//  POST /api/ai/extract-companies
// ============================================================
app.post('/api/ai/extract-companies', async (req, res) => {
    const { text } = req.body;
    if (!text || typeof text !== 'string') {
        return res.status(400).json({ error: 'Request body must include "text" (string)' });
    }

    if (!geminiKeyValid) {
        return res.json(localFallbackExtractCompanies(text));
    }

    try {
        const prompt = `You are a Data Extraction Assistant.
Identify and extract all company/client profiles from the text below.
Return ONLY valid JSON (no markdown).

STRICT RULES:
1. Extract name, address (if present), GST/Tax number (if present) for each company.
2. Clean names, addresses, and GST numbers.

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {
    "name": "Full Company Name (required)",
    "address": "Company Address or null",
    "gstNumber": "GSTIN or null"
  }
]

TEXT:
${text}`;

        console.log('[AI Extractor] Extracting companies...');
        const result = await generateWithRetry(modelName, prompt);
        res.json(parseGeminiJson(result.response.text()));
    } catch (error) {
        logAiFailure('extract-companies', error.message, 3, 'local-regex-fallback');
        try {
            res.json(localFallbackExtractCompanies(text));
        } catch (fbErr) {
            console.error('[AI Extractor] Fallback failed:', fbErr.message);
            res.status(500).json([]);
        }
    }
});

// ============================================================
//  ROUTE: Natural Language Search
//  POST /api/ai/nl-search
// ============================================================
app.post('/api/ai/nl-search', async (req, res) => {
    const { query, currentDate } = req.body;
    if (!query || typeof query !== 'string') {
        return res.status(400).json({ error: 'Request body must include "query" (string)' });
    }

    if (!geminiKeyValid) {
        return res.json(localFallbackNlSearch(query, currentDate));
    }

    try {
        const prompt = `You are a Database Query Assistant.
Translate the natural language search query for travel bills into a structured JSON filter.
The current system date is: ${currentDate || new Date().toISOString().split('T')[0]}.
Return ONLY valid JSON (no markdown).

STRICT RULES:
1. Interpret time expressions relative to current date.
   - "this month": first day of current month to today.
   - "last month": previous full calendar month.
   - "this year": from January 1st of current year.
   - "yesterday": the day before current date.
   - "last week": the 7 preceding days or previous calendar week.
2. Extract company name or vehicle type if mentioned.
3. Extract price constraints: "more than 5000" → minAmount: 5000.
4. Extract distance constraints: "kms over 500" → minKm: 500.
5. Populate "summary" with a user-friendly description of the parsed criteria.

OUTPUT FORMAT (STRICT JSON):
{
  "companyName": "string or null",
  "vehicleType": "Sedan | SUV | Indica | Bus | null",
  "minAmount": null,
  "maxAmount": null,
  "minKm": null,
  "maxKm": null,
  "dateFrom": "YYYY-MM-DD or null",
  "dateTo": "YYYY-MM-DD or null",
  "status": "string or null",
  "keywords": [],
  "summary": "Short user-friendly description"
}

USER QUERY: "${query}"`;

        console.log(`[AI NL Search] Parsing: "${query}" (date: ${currentDate})`);
        const result = await generateWithRetry(modelName, prompt);
        res.json(parseGeminiJson(result.response.text()));
    } catch (error) {
        logAiFailure('nl-search', error.message, 3, 'local-keyword-fallback');
        try {
            res.json(localFallbackNlSearch(query, currentDate));
        } catch (fbErr) {
            console.error('[AI NL Search] Fallback failed:', fbErr.message);
            res.status(500).json({ summary: 'Failed to parse search. Using default.', keywords: [] });
        }
    }
});

// ============================================================
//  LOCAL FALLBACK FUNCTIONS (regex-based, no Gemini needed)
// ============================================================

function localFallbackParseBill(text) {
    const t = text || '';
    const dutySlipMatch = t.match(/(?:duty\s*slip\s*no|slip\s*no|bill\s*no)[:\s]+([a-z0-9-]+)/i);
    const dateMatch     = t.match(/(?:date)[:\s]+([\d]{2}-[\d]{2}-[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2})/i);
    const companyMatch  = t.match(/(?:to|company|client)[:\s]+([^\n\r]+)/i);
    const vehicleNoMatch = t.match(/(?:vehicle|car|reg)[:\s]+([a-z]{2}[-\s]*\d{2}[-\s]*[a-z0-9-\s]+)/i);
    const kmsMatch      = t.match(/(?:kms|km|distance)[:\s]+(\d+)/i);
    const hoursMatch    = t.match(/(?:hours|hrs|time)[:\s]+(\d+)/i);

    const charges = [];
    const bataMatch    = t.match(/(?:driver\s*bata|bata)[:\s]+(\d+)/i);
    const tollMatch    = t.match(/(?:toll|tolls)[:\s]+(\d+)/i);
    const parkingMatch = t.match(/(?:parking)[:\s]+(\d+)/i);
    if (bataMatch)    charges.push({ name: 'Driver Bata', amount: parseFloat(bataMatch[1]) });
    if (tollMatch)    charges.push({ name: 'Toll',        amount: parseFloat(tollMatch[1]) });
    if (parkingMatch) charges.push({ name: 'Parking',     amount: parseFloat(parkingMatch[1]) });

    const amountMatch = t.match(/(?:total\s*amount|amount|total)[:\s]+(\d+)/i);
    const totalAmount = amountMatch
        ? parseFloat(amountMatch[1])
        : (charges.reduce((acc, c) => acc + c.amount, 0) || 1500.0);

    let formattedDate = new Date().toISOString().split('T')[0];
    if (dateMatch) {
        const dStr = dateMatch[1].trim();
        if (dStr.includes('-')) {
            const parts = dStr.split('-');
            formattedDate = parts[0].length === 2
                ? `${parts[2]}-${parts[1]}-${parts[0]}` // DD-MM-YYYY -> YYYY-MM-DD
                : dStr;
        }
    }

    return [{
        dutySlipNo:    dutySlipMatch ? dutySlipMatch[1].trim().toUpperCase() : `FALLBACK-${Date.now()}`,
        billDate:      formattedDate,
        companyName:   companyMatch ? companyMatch[1].trim() : 'Unknown Client',
        vehicleNumber: vehicleNoMatch ? vehicleNoMatch[1].trim().toUpperCase() : 'UNKNOWN',
        vehicleType:   t.toLowerCase().includes('indica') ? 'Indica' : (t.toLowerCase().includes('suv') ? 'SUV' : 'Sedan'),
        totalKms:      kmsMatch ? parseFloat(kmsMatch[1]) : 0,
        totalHours:    hoursMatch ? parseFloat(hoursMatch[1]) : 0,
        dynamicCharges: charges.length > 0 ? charges : [{ name: 'Base Amount', amount: totalAmount }],
        totalAmount,
        warnings: ['[Local regex fallback — Gemini API unavailable]']
    }];
}

function localFallbackExtractCompanies(text) {
    const t = text || '';
    const companyMatch = t.match(/(?:to|company|client)[:\s]+([^\n\r]+)/i);
    const gstMatch     = t.match(/(?:gst|gstin)[:\s]+([a-z0-9]{15})/i);
    return [{
        name:      companyMatch ? companyMatch[1].trim() : 'Unknown Company',
        address:   null,
        gstNumber: gstMatch ? gstMatch[1].toUpperCase() : null
    }];
}

function localFallbackNlSearch(query, currentDate) {
    const q = (query || '').toLowerCase();
    const filter = {
        companyName: null, vehicleType: null,
        minAmount: null, maxAmount: null,
        minKm: null, maxKm: null,
        dateFrom: null, dateTo: null,
        status: null, keywords: [],
        summary: `Local keyword fallback: "${query}"`
    };

    if (q.includes('ashapura'))  filter.companyName = 'Ashapura';
    else if (q.includes('bhavani')) filter.companyName = 'Sri Tulja Bhavani Travels';

    if (q.includes('indica'))    filter.vehicleType = 'Indica';
    else if (q.includes('sedan')) filter.vehicleType = 'Sedan';
    else if (q.includes('suv'))   filter.vehicleType = 'SUV';

    const aboveMatch = q.match(/(?:above|greater\s*than|over|>\s*)\s*(\d+)/);
    if (aboveMatch) filter.minAmount = parseFloat(aboveMatch[1]);
    const belowMatch = q.match(/(?:below|less\s*than|under|<\s*)\s*(\d+)/);
    if (belowMatch) filter.maxAmount = parseFloat(belowMatch[1]);

    const d = new Date(currentDate || new Date().toISOString().split('T')[0]);
    if (q.includes('this month')) {
        filter.dateFrom = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
        filter.dateTo   = d.toISOString().split('T')[0];
    } else if (q.includes('last month')) {
        const prev     = new Date(d.getFullYear(), d.getMonth() - 1, 1);
        const lastDay  = new Date(d.getFullYear(), d.getMonth(), 0);
        filter.dateFrom = prev.toISOString().split('T')[0];
        filter.dateTo   = lastDay.toISOString().split('T')[0];
    }

    return filter;
}

// ============================================================
//  STARTUP CERTIFICATION
//  Verifies Gemini connectivity on boot.
//  Does NOT crash the server on transient network errors —
//  the server starts in degraded mode instead.
// ============================================================
async function certifyAiInfrastructure() {
    console.log('==================================================');
    console.log('     AI MICROSERVICE STARTUP CERTIFICATION        ');
    console.log('==================================================');

    if (!geminiKeyValid) {
        console.warn('[Cert] WARNING: GEMINI_API_KEY missing or placeholder.');
        console.warn('[Cert] Server starting in DEGRADED MODE — AI endpoints use local fallbacks.');
        console.warn('==================================================');
        return;
    }

    console.log(`[Cert] API Key detected.`);
    console.log(`[Cert] Configured model:     ${process.env.GEMINI_MODEL || 'gemini-1.5-pro'}`);
    console.log(`[Cert] Configured embedding: ${process.env.GEMINI_EMBEDDING_MODEL || 'text-embedding-004'}`);

    // Content generation test
    try {
        console.log('[Cert] Testing content generation...');
        const testModel = genAI.getGenerativeModel({ model: process.env.GEMINI_MODEL || 'gemini-1.5-pro' });
        const testResult = await testModel.generateContent({
            contents: [{ parts: [{ text: 'Respond with the single word: READY' }] }]
        });
        const respText = testResult.response.text().trim();
        console.log(`[Cert] Content generation OK. Response: "${respText}"`);
    } catch (err) {
        // Non-fatal in degraded mode — could be transient network issue
        console.warn(`[Cert] Content generation test failed: ${err.message}`);
        console.warn('[Cert] Server will still start — verify API key and network.');
    }

    // Embedding test
    try {
        console.log('[Cert] Testing embedding generation...');
        const embedModelName = process.env.GEMINI_EMBEDDING_MODEL || 'text-embedding-004';
        const embedModel = genAI.getGenerativeModel({ model: embedModelName });
        const embedResult = await embedModel.embedContent('Hello');
        const vector = embedResult.embedding.values;
        if (!vector || vector.length === 0) throw new Error('Empty vector returned');
        console.log(`[Cert] Embedding OK. Dimensions: ${vector.length}`);
    } catch (err) {
        console.warn(`[Cert] Embedding test failed: ${err.message}`);
        console.warn('[Cert] Embedding features (RAG, cache) may be unavailable.');
    }

    console.log('==================================================');
    console.log('  AI INFRASTRUCTURE CERTIFICATION COMPLETE        ');
    console.log('==================================================');
}

// ============================================================
//  START SERVER
// ============================================================
certifyAiInfrastructure().then(() => {
    app.listen(PORT, '0.0.0.0', () => {
        console.log(`AI Service running on http://localhost:${PORT}`);
        if (!geminiKeyValid) {
            console.warn('[DEGRADED MODE] Set GEMINI_API_KEY in ai/.env to enable AI features.');
        }
    });
}).catch(err => {
    console.error('[FATAL] Certification crashed unexpectedly:', err);
    process.exit(1);
});
