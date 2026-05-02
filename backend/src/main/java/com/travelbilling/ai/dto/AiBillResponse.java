package com.travelbilling.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiBillResponse {
    private String dutySlipNo; // Was billNumber
    private String billDate;   // Was date
    private String companyName;
    private String vehicleNumber;
    private String vehicleType;
    private Double totalKms;   // Was totalKm
    private Double totalHours;
    private List<Charge> dynamicCharges; // Was charges
    private Double totalAmount;
    private List<String> warnings;

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Charge {
        private String name;
        private Double amount;
    }
}
