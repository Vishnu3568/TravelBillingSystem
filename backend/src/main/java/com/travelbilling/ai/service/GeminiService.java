package com.travelbilling.ai.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.ai.dto.AiBillResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class GeminiService {

    @Value("${google.ai.api-key}")
    private String apiKey;

    @Value("${google.ai.model}")
    private String model;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper;

    public AiBillResponse parseBillText(String rawText) {
        if ("REPLACE_WITH_YOUR_GEMINI_API_KEY".equals(apiKey)) {
             return AiBillResponse.builder()
                    .warnings(List.of("Gemini API key not configured. Please set google.ai.api-key in application.properties."))
                    .build();
        }

        String url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + apiKey;

        String prompt = "You are a professional travel bill parsing assistant. Extract data from the following travel bill text and return it in a STRICT JSON format.\n\n" +
                "Rules:\n" +
                "- Do NOT hallucinate values.\n" +
                "- If data is missing, return null.\n" +
                "- Extract all charge rows (Driver Bata, Toll, Parking, Base Amount, etc.).\n" +
                "- Maintain numeric accuracy.\n" +
                "- Add warnings for uncertain or missing fields.\n\n" +
                "Desired JSON Format:\n" +
                "{\n" +
                "  \"billNumber\": \"\",\n" +
                "  \"date\": \"\",\n" +
                "  \"companyName\": \"\",\n" +
                "  \"vehicleNumber\": \"\",\n" +
                "  \"vehicleType\": \"\",\n" +
                "  \"totalKm\": 0,\n" +
                "  \"totalHours\": 0,\n" +
                "  \"charges\": [\n" +
                "    { \"name\": \"\", \"amount\": 0 }\n" +
                "  ],\n" +
                "  \"totalAmount\": 0,\n" +
                "  \"warnings\": []\n" +
                "}\n\n" +
                "Text to parse:\n" +
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
            
            log.info("Sending request to Gemini API...");
            Map<String, Object> response = restTemplate.postForObject(url, entity, Map.class);

            if (response != null && response.containsKey("candidates")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
                if (candidates.isEmpty()) throw new RuntimeException("No candidates in Gemini response");
                
                Map<String, Object> firstCandidate = candidates.get(0);
                Map<String, Object> content = (Map<String, Object>) firstCandidate.get("content");
                List<Map<String, Object>> resParts = (List<Map<String, Object>>) content.get("parts");
                String jsonResponse = (String) resParts.get(0).get("text");

                // Clean up JSON if AI adds Markdown blocks
                jsonResponse = jsonResponse.replaceAll("```json", "").replaceAll("```", "").trim();

                return objectMapper.readValue(jsonResponse, AiBillResponse.class);
            }
        } catch (Exception e) {
            log.error("Gemini AI parsing failed", e);
            return AiBillResponse.builder()
                    .warnings(List.of("AI Parsing Error: " + e.getMessage()))
                    .build();
        }
        return AiBillResponse.builder()
                .warnings(List.of("Empty response from AI"))
                .build();
    }
}
