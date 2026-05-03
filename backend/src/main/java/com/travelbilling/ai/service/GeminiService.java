package com.travelbilling.ai.service;

import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.ai.dto.AiSearchFilter;
import com.travelbilling.ai.dto.AiInsightResponse;
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

    public AiSearchFilter parseSearchQuery(String query) {
        try {
            Map<String, String> request = new HashMap<>();
            request.put("query", query);
            request.put("currentDate", java.time.LocalDate.now().toString());

            log.info("Delegating NL search parsing to AI Service (Port 9001)...");
            return restTemplate.postForObject(aiServiceUrl + "/nl-search", request, AiSearchFilter.class);
        } catch (Exception e) {
            log.error("Failed to parse search query via AI", e);
            return null;
        }
    }

    public AiInsightResponse generateInsights(com.travelbilling.dto.DashboardStatsDTO stats) {
        try {
            Map<String, Object> request = new HashMap<>();
            request.put("stats", stats);

            log.info("Delegating insights generation to AI Service (Port 9001)...");
            return restTemplate.postForObject(aiServiceUrl + "/generate-insights", request, AiInsightResponse.class);
        } catch (Exception e) {
            log.error("Failed to generate insights via AI", e);
            return AiInsightResponse.builder()
                    .insights(List.of(AiInsightResponse.Insight.builder()
                            .type("WARNING")
                            .message("AI Insights Service currently unavailable.")
                            .confidence(0.0)
                            .build()))
                    .build();
        }
    }
}
