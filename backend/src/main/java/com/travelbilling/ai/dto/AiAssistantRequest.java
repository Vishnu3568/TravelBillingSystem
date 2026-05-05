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
public class AiAssistantRequest {
    private String contextType; // BILL | GLOBAL
    private BillData billData;
    private AggregatedData aggregatedData;
    private String userQuery;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class BillData {
        private String billNumber;
        private String companyName;
        private Double totalKm;
        private Double totalHours;
        private List<Map<String, Object>> charges;
        private Double totalAmount;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AggregatedData {
        private Double totalRevenue;
        private List<Map<String, Object>> topCompanies;
        private List<Map<String, Object>> recentBills;
    }
}
