package com.travels.billing.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.travels.billing.model.ExtractedBillDto;
import com.travels.billing.model.ParsedBill;
import com.travels.billing.repository.BillRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Optional;
import java.util.UUID;

@Service
public class DatabasePersistenceService {
    private static final Logger logger = LoggerFactory.getLogger(DatabasePersistenceService.class);
    
    @Autowired
    private BillRepository billRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Transactional
    public ParsedBill saveBill(ExtractedBillDto dto, String createdBy) throws Exception {
        if (dto == null) {
            throw new IllegalArgumentException("Cannot save a null bill.");
        }

        // Check for duplicates before database insert
        String dsNo = dto.getDutySlipNumber();
        String compName = dto.getCompany();
        
        if (dsNo != null && compName != null) {
            Optional<ParsedBill> existing = billRepository.findByDutySlipNoAndCompanyName(dsNo.trim(), compName.trim());
            if (existing.isPresent()) {
                logger.warn("Duplicate bill ignored: Duty Slip '{}' for company '{}' already exists.", dsNo, compName);
                throw new IllegalStateException("Duplicate bill: Duty Slip '" + dsNo + "' already exists.");
            }
        }

        // Map DTO to Database Entity
        ParsedBill bill = new ParsedBill();
        
        // Generate Bill Number if missing
        if (dto.getBillNumber() != null && !dto.getBillNumber().trim().isEmpty()) {
            bill.setBillNumber(dto.getBillNumber().trim());
        } else {
            bill.setBillNumber("BILL-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        }

        // Date conversions
        bill.setBillDate(LocalDateTime.now());
        bill.setCompanyName(compName);
        bill.setVehicleName(dto.getVehicleNumber());
        bill.setDutySlipNo(dsNo);
        
        if (dto.getReportingDate() != null) {
            try {
                bill.setTripDate(LocalDate.parse(dto.getReportingDate().trim()));
            } catch (Exception e) {
                bill.setTripDate(LocalDate.now());
            }
        } else {
            bill.setTripDate(LocalDate.now());
        }
        
        bill.setVehicleType(dto.getVehicleType());
        bill.setAcNonAc("AC"); // Default
        bill.setTotalKms(dto.getTotalKilometers() != null ? dto.getTotalKilometers() : 0.0);
        bill.setTotalHours(dto.getTotalHours() != null ? dto.getTotalHours() : 0.0);
        bill.setExtraKms(dto.getExtraKilometers() != null ? dto.getExtraKilometers() : 0.0);
        bill.setExtraHours(dto.getExtraHours() != null ? dto.getExtraHours() : 0.0);
        bill.setTripType("Local"); // Default
        bill.setPricingType("BASE");
        
        bill.setBaseAmount(dto.getBaseAmount() != null ? dto.getBaseAmount() : 0.0);
        bill.setDriverBata(dto.getDriverBata() != null ? dto.getDriverBata() : 0.0);
        bill.setNightCharges(dto.getNightCharges() != null ? dto.getNightCharges() : 0.0);
        bill.setOtherCharges((dto.getParking() != null ? dto.getParking() : 0.0)
                + (dto.getToll() != null ? dto.getToll() : 0.0)
                + (dto.getPermit() != null ? dto.getPermit() : 0.0)
                + (dto.getOtherCharges() != null ? dto.getOtherCharges() : 0.0));
        
        bill.setNotes(dto.getRemarks());
        
        // Serialize nested dynamic charges to JSON string
        if (dto.getDynamicCharges() != null) {
            bill.setDynamicCharges(objectMapper.writeValueAsString(dto.getDynamicCharges()));
        } else {
            bill.setDynamicCharges("[]");
        }

        bill.setContactPerson(dto.getDriver());
        bill.setBookedBy(createdBy);
        bill.setManagerName("AI Parser");
        bill.setGrandTotal(dto.getTotalAmount() != null ? dto.getTotalAmount() : 0.0);
        bill.setCreatedBy(createdBy);
        bill.setCreatedAt(LocalDateTime.now());
        bill.setUpdatedAt(LocalDateTime.now());

        return billRepository.save(bill);
    }
}
