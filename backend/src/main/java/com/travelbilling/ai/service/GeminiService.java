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

        String url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + apiKey;

        String prompt = "You are an expert bill auditor for 'Sri Tulja Bhavani Travels'. Process this document text with surgical precision.\n\n" +
                "EXTRACTION RULES:\n" +
                "1. CLIENT IDENTIFICATION: Look for 'To,' or 'To'. The text immediately following this is the CLIENT COMPANY. Ignore 'Sri Tulja Bhavani Travels' as that is the provider.\n" +
                "2. VEHICLE DATA: Split combined strings like 'Crysta6673'. Type='Crysta', Number='6673'.\n" +
                "3. CHARGE RESOLUTION: Extract specific amounts for 'Toll', 'Parking', 'Bata', 'Permit'. If they are bunched (e.g. 'Toll500Bata200'), separate them.\n" +
                "4. DATES: Convert all dates to YYYY-MM-DD format.\n" +
                "5. TRIP METRICS: 'totalKms' and 'totalHours' must be numbers. If 'OutStation' is mentioned, set hours to 0.\n" +
                "6. DUTY SLIP: Find 'Duty Slip No' or 'DS No'. This is mandatory.\n\n" +
                "TEXT TO PROCESS:\n" +
                rawText;

        try {
            // Build the JSON schema for response enforcement
            Map<String, Object> responseSchema = new HashMap<>();
            responseSchema.put("type", "array");
            Map<String, Object> items = new HashMap<>();
            items.put("type", "object");
            Map<String, Object> properties = new HashMap<>();
            properties.put("dutySlipNo", Map.of("type", "string"));
            properties.put("billDate", Map.of("type", "string"));
            properties.put("companyName", Map.of("type", "string"));
            properties.put("vehicleNumber", Map.of("type", "string"));
            properties.put("vehicleType", Map.of("type", "string"));
            properties.put("totalKms", Map.of("type", "number"));
            properties.put("totalHours", Map.of("type", "number"));
            
            Map<String, Object> chargeItems = new HashMap<>();
            chargeItems.put("type", "object");
            chargeItems.put("properties", Map.of(
                "name", Map.of("type", "string"),
                "amount", Map.of("type", "number")
            ));
            properties.put("dynamicCharges", Map.of("type", "array", "items", chargeItems));
            properties.put("totalAmount", Map.of("type", "number"));
            properties.put("warnings", Map.of("type", "array", "items", Map.of("type", "string")));
            
            items.put("properties", properties);
            items.put("required", List.of("dutySlipNo", "billDate", "companyName", "vehicleNumber", "totalAmount"));
            responseSchema.put("items", items);

            Map<String, Object> generationConfig = new HashMap<>();
            generationConfig.put("response_mime_type", "application/json");
            generationConfig.put("response_schema", responseSchema);

            Map<String, Object> requestBody = new HashMap<>();
            Map<String, Object> contents = new HashMap<>();
            Map<String, Object> parts = new HashMap<>();
            parts.put("text", prompt);
            contents.put("parts", List.of(parts));
            requestBody.put("contents", List.of(contents));
            requestBody.put("generationConfig", generationConfig);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            
            log.info("Sending request to Gemini API with Response Schema...");
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);

            if (response != null && response.containsKey("candidates")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
                if (candidates.isEmpty()) throw new RuntimeException("No candidates in Gemini response");
                
                Map<String, Object> firstCandidate = candidates.get(0);
                Map<String, Object> content = (Map<String, Object>) firstCandidate.get("content");
                List<Map<String, Object>> resParts = (List<Map<String, Object>>) content.get("parts");
                String jsonResponse = (String) resParts.get(0).get("text");

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
        String url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + apiKey;
        
        String prompt = "Extract all unique client companies from the following text.\n" +
                "For each company, find their Name, Address, and GST Number (if available).\n" +
                "Rule: Ignore 'Sri Tulja Bhavani Travels'.\n\n" +
                "Text:\n" +
                rawText;

        try {
            Map<String, Object> responseSchema = new HashMap<>();
            responseSchema.put("type", "array");
            Map<String, Object> items = new HashMap<>();
            items.put("type", "object");
            items.put("properties", Map.of(
                "name", Map.of("type", "string"),
                "address", Map.of("type", "string"),
                "gstNumber", Map.of("type", "string")
            ));
            responseSchema.put("items", items);

            Map<String, Object> generationConfig = new HashMap<>();
            generationConfig.put("response_mime_type", "application/json");
            generationConfig.put("response_schema", responseSchema);

            Map<String, Object> requestBody = new HashMap<>();
            Map<String, Object> contents = new HashMap<>();
            Map<String, Object> parts = new HashMap<>();
            parts.put("text", prompt);
            contents.put("parts", List.of(parts));
            requestBody.put("contents", List.of(contents));
            requestBody.put("generationConfig", generationConfig);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);

            if (response != null && response.containsKey("candidates")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
                Map<String, Object> content = (Map<String, Object>) candidates.get(0).get("content");
                List<Map<String, Object>> resParts = (List<Map<String, Object>>) content.get("parts");
                String jsonResponse = (String) resParts.get(0).get("text");

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
