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

app.listen(port, () => {
    console.log(`\n============================================`);
    console.log(`🚀 AI Service running on http://localhost:${port}`);
    console.log(`🎯 Model: ${modelName}`);
    console.log(`============================================\n`);
});
