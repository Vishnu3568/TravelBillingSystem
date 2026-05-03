package com.travelbilling.ai.service;

import com.travelbilling.ai.dto.AiBillResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class GeminiService {

    private final RestTemplate restTemplate;

    public GeminiService() {
        this.restTemplate = new RestTemplateBuilder()
                .setConnectTimeout(java.time.Duration.ofMinutes(5))
                .setReadTimeout(java.time.Duration.ofMinutes(5))
                .build();
    }

    private final String aiServiceUrl = "http://localhost:9001/api/ai";

    public List<AiBillResponse> parseBillText(String rawText) {
        try {
            Map<String, String> request = new HashMap<>();
            request.put("text", rawText);

            log.info("Delegating parsing request to AI Service (Port 9001)...");
            AiBillResponse[] response = restTemplate.postForObject(aiServiceUrl + "/parse-bill", request, AiBillResponse[].class);

            return response != null ? List.of(response) : List.of();
        } catch (Exception e) {
            log.error("Failed to connect to AI Service", e);
            return List.of(AiBillResponse.builder()
                    .warnings(List.of("AI Service Connection Error: " + e.getMessage() + ". Ensure AI service is running on port 9001."))
                    .build());
        }
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, String>> extractCompanies(String rawText) {
        try {
            Map<String, String> request = new HashMap<>();
            request.put("text", rawText);

            log.info("Delegating company extraction to AI Service (Port 9001)...");
            List<Map<String, String>> response = restTemplate.postForObject(aiServiceUrl + "/extract-companies", request, List.class);

            return response != null ? response : List.of();
        } catch (Exception e) {
            log.error("Failed to connect to AI Service", e);
            return List.of();
        }
    }
}
