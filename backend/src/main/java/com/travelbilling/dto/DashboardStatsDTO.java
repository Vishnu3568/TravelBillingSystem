package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;
import java.util.List;

@lombok.Getter
@lombok.Setter
@lombok.ToString
@lombok.EqualsAndHashCode
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

    @lombok.Getter
    @lombok.Setter
    @lombok.ToString
    @lombok.EqualsAndHashCode
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class StatEntry {
        private String name;
        private Double amount;
        private Long count;
    }
}
