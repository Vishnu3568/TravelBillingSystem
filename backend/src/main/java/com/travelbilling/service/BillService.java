package com.travelbilling.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.dto.BillRequest;
import com.travelbilling.dto.BillResponse;
import com.travelbilling.dto.ChargeDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.BillRepository;
import java.security.SecureRandom;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import jakarta.persistence.criteria.Predicate;

@Service
@RequiredArgsConstructor
@Slf4j
public class BillService {
    private static final DateTimeFormatter BILL_NUMBER_DATE = DateTimeFormatter.BASIC_ISO_DATE;
    private static final SecureRandom RANDOM = new SecureRandom();

    private final BillRepository billRepository;
    private final AuditLogService auditLogService;
    private final ObjectMapper objectMapper;

    @Transactional
    public BillResponse createBill(BillRequest request, String createdBy) {
        double grandTotal = calculateGrandTotal(request);
        LocalDateTime billDateTime = request.getBillDate().atStartOfDay();

        Bill bill = Bill.builder()
                .billNumber(generateBillNumber())
                .billDate(billDateTime)
                .amount(grandTotal)
                .companyName(request.getCompanyName().trim())
                .vehicleName(request.getVehicleName().trim())
                .dutySlipNo(request.getDutySlipNo().trim())
                .tripDate(request.getTripDate() != null ? request.getTripDate().atStartOfDay() : null)
                .vehicleType(request.getVehicleType())
                .acNonAc(request.getAcNonAc())
                .totalKms(safeAmount(request.getTotalKms()))
                .totalHours(safeAmount(request.getTotalHours()))
                .extraKms(safeAmount(request.getExtraKms()))
                .extraHours(safeAmount(request.getExtraHours()))
                .tripType(request.getTripType())
                .notes(request.getNotes())
                .dynamicCharges(serializeCharges(request.getDynamicCharges()))
                .grandTotal(grandTotal)
                .createdBy(createdBy)
                .contactPerson(request.getContactPerson())
                .bookedBy(request.getBookedBy())
                .managerName(request.getManagerName())
                .build();
        
        populateHardcodedFields(bill, request);

        Bill saved = billRepository.save(bill);
        auditLogService.logAction("CREATE_BILL", "BILL", "Bill " + saved.getBillNumber() + " created for " + saved.getCompanyName());
        return toResponse(saved);
    }

    @Transactional
    public BillResponse updateBill(Long id, BillRequest request) {
        Bill bill = billRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));

        double grandTotal = calculateGrandTotal(request);
        
        bill.setBillDate(request.getBillDate().atStartOfDay());
        bill.setCompanyName(request.getCompanyName().trim());
        bill.setVehicleName(request.getVehicleName().trim());
        bill.setDutySlipNo(request.getDutySlipNo().trim());
        bill.setTripDate(request.getTripDate() != null ? request.getTripDate().atStartOfDay() : null);
        bill.setVehicleType(request.getVehicleType());
        bill.setAcNonAc(request.getAcNonAc());
        bill.setTotalKms(safeAmount(request.getTotalKms()));
        bill.setTotalHours(safeAmount(request.getTotalHours()));
        bill.setExtraKms(safeAmount(request.getExtraKms()));
        bill.setExtraHours(safeAmount(request.getExtraHours()));
        bill.setTripType(request.getTripType());
        bill.setDynamicCharges(serializeCharges(request.getDynamicCharges()));
        bill.setNotes(request.getNotes());
        bill.setGrandTotal(grandTotal);
        bill.setContactPerson(request.getContactPerson());
        bill.setBookedBy(request.getBookedBy());
        bill.setManagerName(request.getManagerName());

        populateHardcodedFields(bill, request);

        Bill saved = billRepository.save(bill);
        auditLogService.logAction("UPDATE_BILL", "BILL", "Bill " + saved.getBillNumber() + " updated");
        return toResponse(saved);
    }

    @Transactional
    public void deleteBill(Long id) {
        Bill bill = billRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));
        String billNumber = bill.getBillNumber();
        billRepository.delete(bill);
        auditLogService.logAction("DELETE_BILL", "BILL", "Bill " + billNumber + " deleted");
    }

    @Transactional(readOnly = true)
    public Page<BillResponse> getBills(int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        return billRepository.findAll(pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public Page<BillResponse> searchBills(
            String billNumber,
            String companyName,
            LocalDate fromDate,
            LocalDate toDate,
            int page,
            int size) {
        
        Pageable pageable = PageRequest.of(page, size, Sort.by("billDate").descending());
        
        Specification<Bill> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            if (billNumber != null && !billNumber.isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("billNumber")), "%" + billNumber.toLowerCase().trim() + "%"));
            }
            
            if (companyName != null && !companyName.isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("companyName")), "%" + companyName.toLowerCase().trim() + "%"));
            }
            
            if (fromDate != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("billDate"), fromDate.atStartOfDay()));
            }
            
            if (toDate != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("billDate"), toDate.atTime(23, 59, 59)));
            }
            
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        
        return billRepository.findAll(spec, pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public BillResponse getBillById(Long id) {
        Bill bill = billRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));
        return toResponse(bill);
    }

    private double calculateGrandTotal(BillRequest request) {
        double total = 0;
        
        if (request.getDynamicCharges() != null) {
            total = request.getDynamicCharges().stream()
                    .mapToDouble(c -> safeAmount(c.getAmount()))
                    .sum();
        } else {
            // Fallback for requests without dynamic charges
            total = safeAmount(request.getBaseAmount())
                    + safeAmount(request.getDriverBata())
                    + safeAmount(request.getParking())
                    + safeAmount(request.getToll())
                    + safeAmount(request.getNightCharges())
                    + safeAmount(request.getOtherCharges());
        }
        
        return total;
    }

    private void populateHardcodedFields(Bill bill, BillRequest request) {
        if (request.getDynamicCharges() != null) {
            // Reset hardcoded fields first
            bill.setBaseAmount(0.0);
            bill.setDriverBata(0.0);
            bill.setParking(0.0);
            bill.setToll(0.0);
            bill.setNightCharges(0.0);
            bill.setOtherCharges(0.0);

            for (ChargeDTO charge : request.getDynamicCharges()) {
                if (charge.getName() == null) continue;
                String name = charge.getName().trim().toLowerCase();
                Double amount = safeAmount(charge.getAmount());
                
                if (name.contains("base amount")) bill.setBaseAmount(amount);
                else if (name.contains("driver bata")) bill.setDriverBata(amount);
                else if (name.contains("parking")) bill.setParking(amount);
                else if (name.contains("toll")) bill.setToll(amount);
                else if (name.contains("night")) bill.setNightCharges(amount);
                else if (name.contains("other")) bill.setOtherCharges(amount);
            }
        } else {
            bill.setBaseAmount(safeAmount(request.getBaseAmount()));
            bill.setDriverBata(safeAmount(request.getDriverBata()));
            bill.setParking(safeAmount(request.getParking()));
            bill.setToll(safeAmount(request.getToll()));
            bill.setNightCharges(safeAmount(request.getNightCharges()));
            bill.setOtherCharges(safeAmount(request.getOtherCharges()));
        }
    }

    private String generateBillNumber() {
        String prefix = "BILL-" + LocalDate.now().format(BILL_NUMBER_DATE) + "-";
        String billNumber;
        do {
            billNumber = prefix + String.format("%04d", RANDOM.nextInt(10000));
        } while (billRepository.existsByBillNumber(billNumber));
        return billNumber;
    }

    private BillResponse toResponse(Bill bill) {
        return new BillResponse(
                bill.getId(),
                bill.getBillNumber(),
                bill.getBillDate() == null ? null : bill.getBillDate().toLocalDate(),
                resolveCompanyName(bill),
                resolveVehicleName(bill),
                bill.getDutySlipNo(),
                bill.getTripDate() == null ? null : bill.getTripDate().toLocalDate(),
                bill.getVehicleType(),
                bill.getAcNonAc(),
                safeAmount(bill.getTotalKms()),
                safeAmount(bill.getTotalHours()),
                safeAmount(bill.getExtraKms()),
                safeAmount(bill.getExtraHours()),
                bill.getTripType(),
                safeAmount(bill.getBaseAmount()),
                safeAmount(bill.getDriverBata()),
                safeAmount(bill.getParking()),
                safeAmount(bill.getToll()),
                safeAmount(bill.getNightCharges()),
                safeAmount(bill.getOtherCharges()),
                deserializeCharges(bill.getDynamicCharges()),
                bill.getNotes(),
                safeAmount(bill.getGrandTotal()),
                bill.getCreatedBy(),
                bill.getCreatedAt(),
                bill.getContactPerson(),
                bill.getBookedBy(),
                bill.getManagerName());
    }

    private String resolveCompanyName(Bill bill) {
        if (bill.getCompanyName() != null && !bill.getCompanyName().isBlank()) {
            return bill.getCompanyName();
        }
        return bill.getCompany() == null ? null : bill.getCompany().getName();
    }

    private String resolveVehicleName(Bill bill) {
        if (bill.getVehicleName() != null && !bill.getVehicleName().isBlank()) {
            return bill.getVehicleName();
        }
        return bill.getVehicle() == null ? null : bill.getVehicle().getRegistrationNumber();
    }

    private double safeAmount(Double amount) {
        return amount == null ? 0 : amount;
    }

    private String serializeCharges(List<ChargeDTO> charges) {
        if (charges == null || charges.isEmpty()) return null;
        try {
            return objectMapper.writeValueAsString(charges);
        } catch (JsonProcessingException e) {
            log.error("Error serializing charges", e);
            return null;
        }
    }

    private List<ChargeDTO> deserializeCharges(String chargesJson) {
        if (chargesJson == null || chargesJson.isBlank()) return Collections.emptyList();
        try {
            return objectMapper.readValue(chargesJson, new TypeReference<List<ChargeDTO>>() {});
        } catch (JsonProcessingException e) {
            log.error("Error deserializing charges", e);
            return Collections.emptyList();
        }
    }
}
