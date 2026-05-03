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
public class AiSearchFilter {
    private String companyName;
    private String vehicleType;
    private Double minAmount;
    private Double maxAmount;
    private Double minKm;
    private Double maxKm;
    private String dateFrom;
    private String dateTo;
    private String status;
    private List<String> keywords;
    private String summary;
}
