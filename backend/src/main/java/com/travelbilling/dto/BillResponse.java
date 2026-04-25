package com.travelbilling.dto;

import java.time.LocalDate;
import java.time.LocalDateTime;

public record BillResponse(
        Long id,
        String billNumber,
        LocalDate billDate,
        String companyName,
        String vehicleName,
        String dutySlipNo,
        double totalKms,
        double totalHours,
        double baseAmount,
        double driverBata,
        double parking,
        double toll,
        double nightCharges,
        double otherCharges,
        String notes,
        double grandTotal,
        String createdBy,
        LocalDateTime createdAt) {
}
