package com.travels.billing.service;

import com.travels.billing.model.ExtractedBillDto;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

@Service
public class ValidationService {

    public List<String> validateAndNormalize(ExtractedBillDto dto) {
        List<String> warnings = new ArrayList<>();

        if (dto == null) {
            warnings.add("Empty extracted bill data.");
            return warnings;
        }

        // 1. Normalize Company Names
        if (dto.getCompany() != null) {
            dto.setCompany(dto.getCompany().toUpperCase().trim());
        } else {
            warnings.add("Missing field: companyName");
            dto.setCompany("Unknown Company");
        }

        // 2. Validate & Normalize Vehicle Numbers
        if (dto.getVehicleNumber() != null) {
            String cleaned = dto.getVehicleNumber().replaceAll("[^a-zA-Z0-9-]", "").toUpperCase().trim();
            dto.setVehicleNumber(cleaned);
            if (cleaned.length() < 5) {
                warnings.add("Invalid vehicle number format: " + dto.getVehicleNumber());
            }
        } else {
            warnings.add("Missing field: vehicleNumber");
            dto.setVehicleNumber("UNKNOWN");
        }

        // 3. Normalize Negative Amounts
        dto.setBaseAmount(normalizeNegative(dto.getBaseAmount(), "baseAmount", warnings));
        dto.setDriverBata(normalizeNegative(dto.getDriverBata(), "driverBata", warnings));
        dto.setParking(normalizeNegative(dto.getParking(), "parking", warnings));
        dto.setToll(normalizeNegative(dto.getToll(), "toll", warnings));
        dto.setPermit(normalizeNegative(dto.getPermit(), "permit", warnings));
        dto.setNightCharges(normalizeNegative(dto.getNightCharges(), "nightCharges", warnings));
        dto.setTotalAmount(normalizeNegative(dto.getTotalAmount(), "totalAmount", warnings));

        if (dto.getDynamicCharges() != null) {
            for (ExtractedBillDto.ChargeDto charge : dto.getDynamicCharges()) {
                charge.setAmount(normalizeNegative(charge.getAmount(), "dynamicCharge: " + charge.getName(), warnings));
            }
        }

        // 4. Validate Arithmetic / Cross-Check Totals
        double calculatedTotal = (dto.getBaseAmount() != null ? dto.getBaseAmount() : 0.0)
                + (dto.getDriverBata() != null ? dto.getDriverBata() : 0.0)
                + (dto.getParking() != null ? dto.getParking() : 0.0)
                + (dto.getToll() != null ? dto.getToll() : 0.0)
                + (dto.getPermit() != null ? dto.getPermit() : 0.0)
                + (dto.getNightCharges() != null ? dto.getNightCharges() : 0.0);

        if (dto.getDynamicCharges() != null) {
            for (ExtractedBillDto.ChargeDto charge : dto.getDynamicCharges()) {
                if (charge.getAmount() != null) {
                    calculatedTotal += charge.getAmount();
                }
            }
        }

        double expectedTotal = dto.getTotalAmount() != null ? dto.getTotalAmount() : 0.0;
        if (Math.abs(calculatedTotal - expectedTotal) > 0.1) {
            warnings.add(String.format("Arithmetic mismatch: calculated sum of items is %.2f, but totalAmount is %.2f", 
                    calculatedTotal, expectedTotal));
            // Automatically correct the total if expectedTotal is 0 or unassigned
            if (expectedTotal == 0.0) {
                dto.setTotalAmount(calculatedTotal);
            }
        }

        // 5. Validate Dates
        validateDateString(dto.getReportingDate(), "reportingDate", warnings);
        validateDateString(dto.getReleaseDate(), "releaseDate", warnings);

        return warnings;
    }

    private Double normalizeNegative(Double value, String fieldName, List<String> warnings) {
        if (value == null) return 0.0;
        if (value < 0) {
            warnings.add("Negative amount detected and normalized for: " + fieldName);
            return Math.abs(value);
        }
        return value;
    }

    private void validateDateString(String dateStr, String fieldName, List<String> warnings) {
        if (dateStr == null || dateStr.trim().isEmpty()) {
            warnings.add("Missing date field: " + fieldName);
            return;
        }
        try {
            LocalDate parsed = LocalDate.parse(dateStr.trim(), DateTimeFormatter.ISO_LOCAL_DATE);
            if (parsed.isAfter(LocalDate.now())) {
                warnings.add("Impossible date (future date) detected for " + fieldName + ": " + dateStr);
            }
            if (parsed.isBefore(LocalDate.of(2000, 1, 1))) {
                warnings.add("Impossible date (past date) detected for " + fieldName + ": " + dateStr);
            }
        } catch (DateTimeParseException e) {
            warnings.add("Invalid date format for " + fieldName + " (expected YYYY-MM-DD): " + dateStr);
        }
    }
}
