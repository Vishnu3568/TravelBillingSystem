package com.travelbilling.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiInsightResponse {
    private List<Insight> insights;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Insight {
        private String type; // INFO, WARNING, TREND
        private String message;
        private Double confidence;
    }
}
