package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DashboardStatsDTO {
    private Double totalRevenue;
    private Long billCount;
    private List<StatEntry> companyStats;
    private List<StatEntry> vehicleStats;
    private List<StatEntry> monthlyRevenue;
    private List<StatEntry> chargeStats;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class StatEntry {
        private String name;
        private Double amount;
        private Long count;
    }
}
