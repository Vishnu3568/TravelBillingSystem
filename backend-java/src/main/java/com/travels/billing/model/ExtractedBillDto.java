package com.travels.billing.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ExtractedBillDto {
    private String company;
    private String billNumber;
    private String invoiceNumber;
    private String dutySlipNumber;
    private String vehicleNumber;
    private String vehicleType;
    private String driver;
    private String reportingDate; // e.g. "YYYY-MM-DD"
    private String reportingTime; // e.g. "HH:MM"
    private String releaseDate;
    private String releaseTime;
    private String pickup;
    private String drop;
    private Double totalHours;
    private Double totalKilometers;
    private Double baseAmount;
    private Double otherCharges;
    private Double minimumHours;
    private Double minimumKilometers;
    private Double extraHours;
    private Double extraKilometers;
    private Double parking;
    private Double toll;
    private Double permit;
    private Double nightCharges;
    private Double driverBata;
    private Double totalAmount;
    private String remarks;
    
    // Support nested charges list if parsed by AI
    private List<ChargeDto> dynamicCharges;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ChargeDto {
        private String name;
        private Double amount;
    }
}
