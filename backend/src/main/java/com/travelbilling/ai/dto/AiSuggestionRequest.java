package com.travelbilling.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiSuggestionRequest {
    private CurrentBill currentBill;
    private HistoricalPatterns historicalPatterns;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class CurrentBill {
        private String companyName;
        private String vehicleType;
        private Double totalKm;
        private Double totalHours;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class HistoricalPatterns {
        private Double averageDriverBata;
        private Double averageToll;
        private Double averageParking;
        private List<String> commonCharges;
        private List<Map<String, Object>> recentSimilarBills;
    }
}
