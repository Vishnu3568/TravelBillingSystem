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
    private String billNumber;
    private String date;
    private String companyName;
    private String vehicleNumber;
    private String vehicleType;
    private Double totalKm;
    private Double totalHours;
    private List<Charge> charges;
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
