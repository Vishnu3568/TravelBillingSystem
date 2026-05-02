package com.travelbilling.ai.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.ai.dto.AiBillResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class GeminiService {

    @Value("${google.ai.api-key}")
    private String apiKey;

    @Value("${google.ai.model}")
    private String model;

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public GeminiService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.restTemplate = new RestTemplateBuilder()
                .setConnectTimeout(java.time.Duration.ofMinutes(5))
                .setReadTimeout(java.time.Duration.ofMinutes(5))
                .build();
    }

    public List<AiBillResponse> parseBillText(String rawText) {
        if ("REPLACE_WITH_YOUR_GEMINI_API_KEY".equals(apiKey)) {
             return List.of(AiBillResponse.builder()
                    .warnings(List.of("Gemini API key not configured."))
                    .build());
        }

        // Using v1beta as confirmed by the successful model list test
        String url = "https://generativelanguage.googleapis.com/v1/models/" + model + ":generateContent?key=" + apiKey;

        String prompt = "You are an expert bill auditor. Process this text with surgical precision.\n\n" +
                "EXTRACTION STEPS:\n" +
                "1. FIND CLIENT: Search for the exact word 'To,' or 'To'. The text IMMEDIATELY following 'To,' (usually on the next line) is the Client Company Name. NEVER use 'Sri Tulja Bhavani Travels'.\n" +
                "2. DE-CONCATENATE DATA: If you see a string like 'CrystaA/C6673', split it: Type='Crysta A/C', Number='6673'.\n" +
                "3. RESOLVE CHARGES: If numbers are bunched together (e.g., '2800x205x800Toll5600'), look for keywords like 'Toll', 'Parking', 'Bata'. Extract the specific amount for each keyword.\n" +
                "4. NUMERIC CLEANING: Strip all non-numeric characters from 'totalKms' and 'totalHours'. If it says 'OutStation', treat it as a trip type, not a number of hours (set hours to 0).\n" +
                "5. DUTY SLIP: Find the 'Duty Slip No' or 'DS No'. It is a required field.\n\n" +
                "Return a STRICT JSON ARRAY. Format:\n" +
                "[\n" +
                "  {\n" +
                "    \"dutySlipNo\": \"\",\n" +
                "    \"billDate\": \"YYYY-MM-DD\",\n" +
                "    \"companyName\": \"\",\n" +
                "    \"vehicleNumber\": \"\",\n" +
                "    \"vehicleType\": \"\",\n" +
                "    \"totalKms\": 0,\n" +
                "    \"totalHours\": 0,\n" +
                "    \"dynamicCharges\": [{ \"name\": \"\", \"amount\": 0 }],\n" +
                "    \"totalAmount\": 0,\n" +
                "    \"warnings\": []\n" +
                "  }\n" +
                "]\n\n" +
                "TEXT TO PROCESS:\n" +
                rawText;

        try {
            Map<String, Object> requestBody = new HashMap<>();
            Map<String, Object> contents = new HashMap<>();
            Map<String, Object> parts = new HashMap<>();
            parts.put("text", prompt);
            contents.put("parts", List.of(parts));
            requestBody.put("contents", List.of(contents));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            
            log.info("Sending request to Gemini API (v1)...");
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);

            if (response != null && response.containsKey("candidates")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
                if (candidates.isEmpty()) throw new RuntimeException("No candidates in Gemini response");
                
                Map<String, Object> firstCandidate = candidates.get(0);
                Map<String, Object> content = (Map<String, Object>) firstCandidate.get("content");
                List<Map<String, Object>> resParts = (List<Map<String, Object>>) content.get("parts");
                String jsonResponse = (String) resParts.get(0).get("text");

                jsonResponse = cleanJsonResponse(jsonResponse);

                return objectMapper.readValue(jsonResponse, objectMapper.getTypeFactory().constructCollectionType(List.class, AiBillResponse.class));
            }
        } catch (Exception e) {
            log.error("Gemini AI parsing failed", e);
            return List.of(AiBillResponse.builder()
                    .warnings(List.of("AI Parsing Error: " + e.getMessage()))
                    .build());
        }
        return List.of(AiBillResponse.builder()
                .warnings(List.of("Empty response from AI"))
                .build());
    }

    public List<Map<String, String>> extractCompanies(String rawText) {
        String prompt = "Extract all unique companies from the following text.\n" +
                "For each company, find their Name, Address, and GST Number (if available).\n\n" +
                "Rules:\n" +
                "- Return a STRICT JSON ARRAY of objects.\n" +
                "- Fields: \"name\", \"address\", \"gstNumber\".\n" +
                "- If data is missing, return empty string.\n\n" +
                "Text:\n" +
                rawText;

        try {
            Map<String, Object> requestBody = new HashMap<>();
            Map<String, Object> contents = new HashMap<>();
            Map<String, Object> parts = new HashMap<>();
            parts.put("text", prompt);
            contents.put("parts", List.of(parts));
            requestBody.put("contents", List.of(contents));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            Map<String, Object> response = restTemplate.postForObject(
                "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + apiKey, 
                entity, 
                Map.class
            );

            if (response != null && response.containsKey("candidates")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
                Map<String, Object> content = (Map<String, Object>) candidates.get(0).get("content");
                List<Map<String, Object>> resParts = (List<Map<String, Object>>) content.get("parts");
                String jsonResponse = (String) resParts.get(0).get("text");

                jsonResponse = cleanJsonResponse(jsonResponse);
                return objectMapper.readValue(jsonResponse, objectMapper.getTypeFactory().constructCollectionType(List.class, Map.class));
            }
        } catch (Exception e) {
            log.error("AI Company extraction failed", e);
        }
        return List.of();
    }

    private String cleanJsonResponse(String raw) {
        if (raw == null) return "[]";
        String cleaned = raw.trim();
        
        // Remove Markdown blocks
        cleaned = cleaned.replaceAll("(?s)```json\\s*(.*?)\\s*```", "$1");
        cleaned = cleaned.replaceAll("(?s)```\\s*(.*?)\\s*```", "$1");
        
        // Find the first [ and last ] to extract just the array
        int start = cleaned.indexOf('[');
        int end = cleaned.lastIndexOf(']');
        
        if (start != -1 && end != -1 && end > start) {
            return cleaned.substring(start, end + 1);
        }
        
        return cleaned.trim();
    }
}
