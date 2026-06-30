package com.travels.billing.service;

import com.travels.billing.model.ExtractedBillDto;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

public class ValidationServiceTest {

    private final ValidationService validationService = new ValidationService();

    @Test
    public void testSuccessfulValidation() {
        ExtractedBillDto dto = new ExtractedBillDto();
        dto.setCompany("Ashapura Travels");
        dto.setVehicleNumber("AP-09-TV-1234");
        dto.setReportingDate("2026-06-30");
        dto.setReleaseDate("2026-06-30");
        dto.setBaseAmount(2500.0);
        dto.setDriverBata(300.0);
        dto.setParking(150.0);
        dto.setToll(200.0);
        dto.setTotalAmount(3150.0);

        List<String> warnings = validationService.validateAndNormalize(dto);
        assertTrue(warnings.isEmpty(), "Warnings list should be empty for correct values.");
        assertEquals("ASHAPURA TRAVELS", dto.getCompany());
        assertEquals("AP-09-TV-1234", dto.getVehicleNumber());
    }

    @Test
    public void testArithmeticMismatch() {
        ExtractedBillDto dto = new ExtractedBillDto();
        dto.setCompany("Ashapura Travels");
        dto.setVehicleNumber("AP-09-TV-1234");
        dto.setReportingDate("2026-06-30");
        dto.setReleaseDate("2026-06-30");
        dto.setBaseAmount(2500.0);
        dto.setDriverBata(300.0);
        dto.setParking(150.0);
        dto.setToll(200.0);
        dto.setTotalAmount(5000.0); // Incorrect total

        List<String> warnings = validationService.validateAndNormalize(dto);
        assertFalse(warnings.isEmpty());
        assertTrue(warnings.get(0).contains("Arithmetic mismatch"));
    }

    @Test
    public void testNegativeAmountsNormalized() {
        ExtractedBillDto dto = new ExtractedBillDto();
        dto.setCompany("Ashapura Travels");
        dto.setVehicleNumber("AP-09-TV-1234");
        dto.setReportingDate("2026-06-30");
        dto.setReleaseDate("2026-06-30");
        dto.setBaseAmount(-2500.0); // Negative
        dto.setDriverBata(300.0);
        dto.setParking(150.0);
        dto.setToll(200.0);
        dto.setTotalAmount(3150.0);

        List<String> warnings = validationService.validateAndNormalize(dto);
        assertFalse(warnings.isEmpty());
        assertTrue(warnings.get(0).contains("Negative amount detected"));
        assertEquals(2500.0, dto.getBaseAmount()); // Normalized to positive
    }

    @Test
    public void testImpossibleDatesWarning() {
        ExtractedBillDto dto = new ExtractedBillDto();
        dto.setCompany("Ashapura Travels");
        dto.setVehicleNumber("AP-09-TV-1234");
        dto.setReportingDate("2050-06-30"); // Future impossible date
        dto.setReleaseDate("2026-06-30");
        dto.setBaseAmount(2500.0);
        dto.setDriverBata(300.0);
        dto.setTotalAmount(2800.0);

        List<String> warnings = validationService.validateAndNormalize(dto);
        assertFalse(warnings.isEmpty());
        assertTrue(warnings.get(0).contains("Impossible date"));
    }
}
