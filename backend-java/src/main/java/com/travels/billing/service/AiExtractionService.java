package com.travels.billing.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travels.billing.model.BillChunk;
import com.travels.billing.model.ExtractedBillDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Service
public class AiExtractionService {
    private static final Logger logger = LoggerFactory.getLogger(AiExtractionService.class);

    @Value("${gemini.api.url}")
    private String geminiUrl;

    @Value("${gemini.api.key}")
    private String apiKey;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ExtractedBillDto extractBillData(BillChunk chunk) throws Exception {
        String prompt = buildPrompt(chunk);
        
        // Build request body for Gemini API
        Map<String, Object> part = new HashMap<>();
        part.put("text", prompt);
        
        Map<String, Object> contentNode = new HashMap<>();
        contentNode.put("parts", Collections.singletonList(part));
        
        Map<String, Object> generationConfig = new HashMap<>();
        generationConfig.put("responseMimeType", "application/json");
        
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("contents", Collections.singletonList(contentNode));
        requestBody.put("generationConfig", generationConfig);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        String urlWithKey = geminiUrl + "?key=" + apiKey;
        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);

        // Retry loop implementation (Handles rate limit 429 errors)
        int maxAttempts = 3;
        int delayMs = 3000;
        Exception lastException = null;

        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                logger.info("Sending page {} chunk to Gemini (Attempt {}/{})", chunk.getPageNumber(), attempt, maxAttempts);
                ResponseEntity<String> response = restTemplate.postForEntity(urlWithKey, requestEntity, String.class);
                
                if (response.getStatusCode().is2xxSuccessful()) {
                    return parseGeminiResponse(response.getBody());
                }
            } catch (HttpClientErrorException.TooManyRequests e) {
                logger.warn("Gemini API rate limit hit (429). Retrying in {}ms... (Attempt {}/{})", delayMs, attempt, maxAttempts);
                lastException = e;
                Thread.sleep(delayMs);
                delayMs *= 2; // exponential backoff
            } catch (Exception e) {
                logger.error("Error communicating with Gemini API: {}", e.getMessage());
                lastException = e;
                break; // Break on other connection or client errors
            }
        }
        
        // Fallback or re-throw
        logger.error("AI extraction failed for page {} after all attempts.", chunk.getPageNumber());
        throw new RuntimeException("AI Extraction failed: " + (lastException != null ? lastException.getMessage() : "unknown error"));
    }

    private String buildPrompt(BillChunk chunk) {
        return "You are an expert travel invoice parser. Analyze the following single page text and table of a travel bill (Page " + chunk.getPageNumber() + ").\n\n" +
               "--- PAGE CONTENT ---\n" +
               chunk.getExtractedText() + "\n" +
               "--- END PAGE CONTENT ---\n\n" +
               "Extract the following fields and return exactly as a JSON object matching this schema. If any field is not found or cannot be extracted, return null for that field.\n\n" +
               "SCHEMA REQUIRED:\n" +
               "{\n" +
               "  \"company\": \"(Client company name being billed)\",\n" +
               "  \"billNumber\": \"(Invoice or bill number)\",\n" +
               "  \"invoiceNumber\": \"(Invoice number if separate, else same as billNumber)\",\n" +
               "  \"dutySlipNumber\": \"(Duty slip or run sheet number)\",\n" +
               "  \"vehicleNumber\": \"(Vehicle registration number e.g. AP-09-TV-1234)\",\n" +
               "  \"vehicleType\": \"(Vehicle category e.g. SUV, Innova, Sedan)\",\n" +
               "  \"driver\": \"(Name of driver)\",\n" +
               "  \"reportingDate\": \"(Reporting/Start date in YYYY-MM-DD format)\",\n" +
               "  \"reportingTime\": \"(Reporting time in HH:MM format)\",\n" +
               "  \"releaseDate\": \"(Release/End date in YYYY-MM-DD format)\",\n" +
               "  \"releaseTime\": \"(Release time in HH:MM format)\",\n" +
               "  \"pickup\": \"(Pickup location)\",\n" +
               "  \"drop\": \"(Drop-off location)\",\n" +
               "  \"totalHours\": 12.5,\n" +
               "  \"totalKilometers\": 350.0,\n" +
               "  \"minimumHours\": 8.0,\n" +
               "  \"minimumKilometers\": 80.0,\n" +
               "  \"extraHours\": 4.5,\n" +
               "  \"extraKilometers\": 270.0,\n" +
               "  \"parking\": 150.0,\n" +
               "  \"toll\": 220.0,\n" +
               "  \"permit\": 0.0,\n" +
               "  \"nightCharges\": 100.0,\n" +
               "  \"driverBata\": 300.0,\n" +
               "  \"totalAmount\": 3370.0,\n" +
               "  \"remarks\": \"(Any special trip notes or comments)\",\n" +
               "  \"dynamicCharges\": [\n" +
               "     { \"name\": \"Charge Name\", \"amount\": 100.0 }\n" +
               "  ]\n" +
               "}\n\n" +
               "RULES:\n" +
               "1. Double check all arithmetic values. Make sure they are positive double numbers.\n" +
               "2. Clean up registration numbers (remove spacing/symbols if necessary, keep standard uppercase letters).\n" +
               "3. Return ONLY strict JSON. No markdown formatting, no prefix block like ```json, no trailing text, no explanations.";
    }

    private ExtractedBillDto parseGeminiResponse(String responseBody) throws Exception {
        JsonNode rootNode = objectMapper.readTree(responseBody);
        JsonNode candidates = rootNode.path("candidates");
        if (candidates.isArray() && !candidates.isEmpty()) {
            JsonNode firstCandidate = candidates.get(0);
            String text = firstCandidate.path("content").path("parts").get(0).path("text").asText();
            
            // Clean up potentially returned markdown formatting wrappers
            text = text.trim();
            if (text.startsWith("```json")) {
                text = text.substring(7);
            }
            if (text.endsWith("```")) {
                text = text.substring(0, text.length() - 3);
            }
            text = text.trim();
            
            return objectMapper.readValue(text, ExtractedBillDto.class);
        }
        throw new NoSuchElementException("No candidate response content found in Gemini response payload.");
    }
}
