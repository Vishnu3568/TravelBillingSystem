package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class BillResponse {
    private Long id;
    private String billNumber;
    private LocalDate billDate;
    private String companyName;
    private String vehicleName;
    private String dutySlipNo;
    
    private LocalDate tripDate;
    private String vehicleType;
    private String acNonAc;
    
    private Double totalKms;
    private Double totalHours;
    private Double extraKms;
    private Double extraHours;
    private String tripType;

    private Double baseAmount;
    private Double driverBata;
    private Double parking;
    private Double toll;
    private Double nightCharges;
    private Double otherCharges;
    
    private List<ChargeDTO> dynamicCharges;

    private String notes;
    private Double grandTotal;
    private String createdBy;
    private LocalDateTime createdAt;
    
    private String contactPerson;
    private String bookedBy;
    private String managerName;
}
