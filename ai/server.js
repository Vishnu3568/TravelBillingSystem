const express = require('express');
const cors = require('cors');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

const port = process.env.PORT || 9001;
const apiKey = process.env.GEMINI_API_KEY;
const modelName = process.env.GEMINI_MODEL || 'gemini-1.5-flash';

if (!apiKey) {
    console.error('CRITICAL: GEMINI_API_KEY is not set in environment variables.');
    process.exit(1);
}

const genAI = new GoogleGenerativeAI(apiKey);

// AI Bill Parsing Endpoint
app.post('/api/ai/parse-bill', async (req, res) => {
    try {
        const { text } = req.body;
        if (!text) {
            return res.status(400).json({ error: 'No text provided' });
        }

        const model = genAI.getGenerativeModel({
            model: modelName,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            dutySlipNo: { type: "string" },
                            billDate: { type: "string" },
                            companyName: { type: "string" },
                            vehicleNumber: { type: "string" },
                            vehicleType: { type: "string" },
                            totalKms: { type: "number" },
                            totalHours: { type: "number" },
                            dynamicCharges: {
                                type: "array",
                                items: {
                                    type: "object",
                                    properties: {
                                        name: { type: "string" },
                                        amount: { type: "number" }
                                    }
                                }
                            },
                            totalAmount: { type: "number" },
                            warnings: { type: "array", items: { type: "string" } }
                        },
                        required: ["dutySlipNo", "billDate", "companyName", "vehicleNumber", "totalAmount"]
                    }
                }
            }
        });

        const prompt = `You are an expert bill auditor for 'Sri Tulja Bhavani Travels'. Process this document text with surgical precision.

EXTRACTION RULES:
1. CLIENT IDENTIFICATION: Look for 'To,' or 'To'. The text immediately following this is the CLIENT COMPANY. Ignore 'Sri Tulja Bhavani Travels' as that is the provider.
2. VEHICLE DATA: Split combined strings like 'Crysta6673'. Type='Crysta', Number='6673'.
3. CHARGE RESOLUTION: Extract specific amounts for 'Toll', 'Parking', 'Bata', 'Permit'. If they are bunched (e.g. 'Toll500Bata200'), separate them.
4. DATES: Convert all dates to YYYY-MM-DD format.
5. TRIP METRICS: 'totalKms' and 'totalHours' must be numbers. If 'OutStation' is mentioned, set hours to 0.
6. DUTY SLIP: Find 'Duty Slip No' or 'DS No'. This is mandatory.

TEXT TO PROCESS:
${text}`;

        console.log(`[AI] Processing parsing request for text length: ${text.length}`);
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const parsedData = JSON.parse(response.text());

        res.json(parsedData);
    } catch (error) {
        console.error('[AI] Parsing Error:', error);
        res.status(500).json([{ warnings: [`AI Service Error: ${error.message}`] }]);
    }
});

// AI Company Extraction Endpoint
app.post('/api/ai/extract-companies', async (req, res) => {
    try {
        const { text } = req.body;
        const model = genAI.getGenerativeModel({
            model: modelName,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            name: { type: "string" },
                            address: { type: "string" },
                            gstNumber: { type: "string" }
                        }
                    }
                }
            }
        });

        const prompt = `Extract all unique client companies from the following text.
For each company, find their Name, Address, and GST Number (if available).
Rule: Ignore 'Sri Tulja Bhavani Travels'.

Text:
${text}`;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        res.json(JSON.parse(response.text()));
    } catch (error) {
        console.error('[AI] Company Extraction Error:', error);
        res.status(500).json([]);
    }
});

// AI Natural Language Search Endpoint
app.post('/api/ai/nl-search', async (req, res) => {
    try {
        const { query, currentDate } = req.body;
        if (!query) {
            return res.status(400).json({ error: 'No query provided' });
        }

        const model = genAI.getGenerativeModel({
            model: modelName,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "object",
                    properties: {
                        companyName: { type: "string" },
                        vehicleType: { type: "string" },
                        minAmount: { type: "number" },
                        maxAmount: { type: "number" },
                        minKm: { type: "number" },
                        maxKm: { type: "number" },
                        dateFrom: { type: "string" },
                        dateTo: { type: "string" },
                        status: { type: "string" },
                        keywords: { type: "array", items: { type: "string" } },
                        summary: { type: "string" }
                    }
                }
            }
        });

        const prompt = `Convert the following natural language billing search query into a structured JSON filter.
Today's Date: ${currentDate || new Date().toISOString().split('T')[0]}

RULES:
1. DATE RESOLUTION:
   - "last week" -> range from 7 days ago until today.
   - "this month" -> range from 1st of current month until today.
   - "July" -> range from July 1st to July 31st of the current year (unless otherwise specified).
   - All dates must be in YYYY-MM-DD format.
2. NUMERIC FILTERS:
   - "above 50000" -> set minAmount to 50000.
   - "below 200 km" -> set maxKm to 200.
3. SEARCH REFINEMENT:
   - If a company name is mentioned, put it in companyName.
   - If a vehicle type (Crysta, Bus, Sedan, etc.) is mentioned, put it in vehicleType.
   - Use 'keywords' for any other search terms not fitting specific fields.
4. SUMMARY:
   - Provide a short, friendly summary of the interpreted search in the 'summary' field (e.g., "Searching for bills from Ashapura with amount > 50,000 in July").
5. NULLS: If a field is not mentioned in the query, return null for that field.

QUERY:
"${query}"`;

        console.log(`[AI] Parsing NL Search: "${query}"`);
        const result = await model.generateContent(prompt);
        const response = await result.response;
        res.json(JSON.parse(response.text()));
    } catch (error) {
        console.error('[AI] NL Search Error:', error);
        res.status(500).json({ error: "Failed to parse search query" });
    }
});

// AI Insights & Analytics Endpoint
app.post('/api/ai/generate-insights', async (req, res) => {
    try {
        const { stats } = req.body;
        if (!stats) {
            return res.status(400).json({ error: 'No statistics provided' });
        }

        const model = genAI.getGenerativeModel({
            model: modelName,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "object",
                    properties: {
                        insights: {
                            type: "array",
                            items: {
                                type: "object",
                                properties: {
                                    type: { type: "string", enum: ["INFO", "WARNING", "TREND"] },
                                    message: { type: "string" },
                                    confidence: { type: "number" }
                                }
                            }
                        }
                    }
                }
            }
        });

        const prompt = `You are a Senior Business Analyst for 'Sri Tulja Bhavani Travels'. Analyze the following aggregated billing data and provide meaningful, actionable insights.

DATA:
- Total Revenue: ₹${stats.totalRevenue}
- Bill Count: ${stats.billCount}
- Top Companies: ${JSON.stringify(stats.companyStats)}
- Vehicle Utilization: ${JSON.stringify(stats.vehicleStats)}
- Monthly Trends: ${JSON.stringify(stats.monthlyRevenue)}
- Charge Breakdown: ${JSON.stringify(stats.chargeStats)}

RULES:
1. FOCUS: Revenue contributors, growth/decline, vehicle efficiency, and expense patterns.
2. FORMAT: Short, clear, data-backed messages.
3. LIMIT: Generate 5-8 insights maximum.
4. TYPE:
   - 'INFO' for general facts or top performers.
   - 'WARNING' for anomalies, high costs, or declining trends.
   - 'TREND' for growth patterns or predictions.
5. NO HALLUCINATION: If the data is minimal or empty, provide limited but honest feedback.

RESPONSE:
Strict JSON only.`;

        console.log(`[AI] Generating Business Insights...`);
        const result = await model.generateContent(prompt);
        const response = await result.response;
        res.json(JSON.parse(response.text()));
    } catch (error) {
        console.error('[AI] Insights Generation Error:', error);
        res.status(500).json({ insights: [{ type: "WARNING", message: "Failed to generate business insights at this time.", confidence: 0 }] });
    }
});

// AI Bill Assistant (Chat) Endpoint
app.post('/api/ai/chat-assistant', async (req, res) => {
    try {
        const { contextType, billData, aggregatedData, userQuery } = req.body;
        
        if (!userQuery) {
            return res.status(400).json({ error: 'No query provided' });
        }

        const model = genAI.getGenerativeModel({
            model: modelName,
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "object",
                    properties: {
                        answer: { type: "string" },
                        confidence: { type: "number" },
                        references: { type: "array", items: { type: "string" } }
                    },
                    required: ["answer", "confidence"]
                }
            }
        });

        const contextInfo = contextType === 'BILL' 
            ? `BILL CONTEXT:
               - Bill Number: ${billData.billNumber}
               - Company: ${billData.companyName}
               - Amount: ₹${billData.totalAmount}
               - Distance: ${billData.totalKm} km
               - Time: ${billData.totalHours} hrs
               - Charges: ${JSON.stringify(billData.charges)}`
            : `GLOBAL CONTEXT:
               - Total Revenue: ₹${aggregatedData.totalRevenue}
               - Top Companies: ${JSON.stringify(aggregatedData.topCompanies)}
               - Recent Bills: ${JSON.stringify(aggregatedData.recentBills)}`;

        const prompt = `You are the 'Sri Tulja Bhavani Travels' Billing Assistant.
Answer the user's question accurately based ONLY on the provided data.

${contextInfo}

RULES:
1. Answer ONLY from provided data.
2. DO NOT hallucinate.
3. If data is insufficient, say: "Insufficient data to answer".
4. Keep answers short and clear (max 3-4 lines).
5. Use ₹ for currency.
6. Provide specific data points used in the 'references' array.

USER QUESTION: "${userQuery}"

Strict JSON Response:`;

        console.log(`[AI Assistant] Processing query: "${userQuery}" (${contextType})`);
        const result = await model.generateContent(prompt);
        const response = await result.response;
        res.json(JSON.parse(response.text()));
    } catch (error) {
        console.error('[AI Assistant] Error:', error);
        res.status(500).json({ 
            answer: "I encountered an error while processing your request.", 
            confidence: 0,
            references: [error.message]
        });
    }
});

app.listen(port, () => {
    console.log(`\n============================================`);
    console.log(`🚀 AI Service running on http://localhost:${port}`);
    console.log(`🎯 Model: ${modelName}`);
    console.log(`============================================\n`);
});
