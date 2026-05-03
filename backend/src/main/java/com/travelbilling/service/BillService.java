package com.travelbilling.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.ai.dto.AiSearchFilter;
import com.travelbilling.dto.BillRequest;
import com.travelbilling.dto.BillResponse;
import com.travelbilling.dto.ChargeDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.entity.Company;
import com.travelbilling.entity.Vehicle;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import com.travelbilling.repository.VehicleRepository;
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
import com.travelbilling.ai.service.GeminiService;
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
    private final CompanyRepository companyRepository;
    private final VehicleRepository vehicleRepository;
    private final AuditLogService auditLogService;
    private final ObjectMapper objectMapper;
    private final GeminiService geminiService;

    @Transactional
    public BillResponse createBill(BillRequest request, String createdBy) {
        double grandTotal = calculateGrandTotal(request);
        LocalDateTime billDateTime = request.getBillDate().atStartOfDay();

        // Data Integrity: Find or create company
        Company company = null;
        if (request.getCompanyName() != null && !request.getCompanyName().isBlank()) {
            company = companyRepository.findByName(request.getCompanyName().trim())
                    .orElseGet(() -> {
                        Company newComp = Company.builder()
                                .name(request.getCompanyName().trim())
                                .address("Imported via AI")
                                .build();
                        return companyRepository.save(newComp);
                    });
        }

        // Data Integrity: Find or create vehicle
        Vehicle vehicle = null;
        if (request.getVehicleName() != null && !request.getVehicleName().isBlank()) {
            String regNo = request.getVehicleName().trim();
            vehicle = vehicleRepository.findByRegistrationNumber(regNo)
                    .orElseGet(() -> {
                        Vehicle newVeh = Vehicle.builder()
                                .registrationNumber(regNo)
                                .type(request.getVehicleType() != null ? request.getVehicleType() : "Car")
                                .build();
                        return vehicleRepository.save(newVeh);
                    });
        }

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
                .pricingType(request.getPricingType())
                .notes(request.getNotes())
                .dynamicCharges(serializeCharges(request.getDynamicCharges()))
                .grandTotal(grandTotal)
                .createdBy(createdBy)
                .company(company)
                .vehicle(vehicle)
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
    public List<BillResponse> saveBills(List<BillRequest> requests, String createdBy) {
        List<BillResponse> responses = new ArrayList<>();
        for (BillRequest request : requests) {
            responses.add(createBill(request, createdBy));
        }
        return responses;
    }

    @Transactional
    public List<BillResponse> saveAiParsedBills(List<AiBillResponse> aiResponses, String createdBy) {
        List<BillResponse> responses = new ArrayList<>();
        for (AiBillResponse ai : aiResponses) {
            try {
                BillRequest req = new BillRequest();
                // Map AI fields to BillRequest
                req.setCompanyName(ai.getCompanyName());
                req.setVehicleName(ai.getVehicleNumber());
                req.setVehicleType(ai.getVehicleType());
                req.setTotalKms(ai.getTotalKms() != null ? ai.getTotalKms() : 0.0);
                req.setTotalHours(ai.getTotalHours() != null ? ai.getTotalHours() : 0.0);
                req.setBaseAmount(ai.getTotalAmount() != null ? ai.getTotalAmount() : 0.0);
                
                if (ai.getDutySlipNo() == null || ai.getDutySlipNo().trim().isEmpty() || "---".equals(ai.getDutySlipNo())) {
                    req.setDutySlipNo("AI-" + (System.currentTimeMillis() % 10000));
                } else {
                    req.setDutySlipNo(ai.getDutySlipNo());
                }
                
                req.setTripType("Outstation"); // Default
                req.setPricingType("BASE");    // Default
                
                // Parse Date
                if (ai.getBillDate() != null) {
                    try {
                        req.setBillDate(LocalDate.parse(ai.getBillDate()));
                    } catch (Exception e) {
                        req.setBillDate(LocalDate.now()); // Fallback to today
                    }
                } else {
                    req.setBillDate(LocalDate.now());
                }

                // Map Dynamic Charges to Hardcoded fields
                if (ai.getDynamicCharges() != null) {
                    List<ChargeDTO> dynamic = new ArrayList<>();
                    for (AiBillResponse.Charge c : ai.getDynamicCharges()) {
                        dynamic.add(new ChargeDTO(c.getName(), null, c.getAmount()));
                        
                        String name = c.getName().toLowerCase();
                        if (name.contains("toll")) req.setToll(c.getAmount());
                        else if (name.contains("parking")) req.setParking(c.getAmount());
                        else if (name.contains("driver") || name.contains("bata")) req.setDriverBata(c.getAmount());
                        else if (name.contains("night")) req.setNightCharges(c.getAmount());
                    }
                    req.setDynamicCharges(dynamic);
                }

                responses.add(createBill(req, createdBy));
            } catch (Exception e) {
                log.error("Failed to save individual AI bill: {}", ai.getDutySlipNo(), e);
            }
        }
        return responses;
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
        bill.setPricingType(request.getPricingType());
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
    public Page<BillResponse> searchBillsNL(String queryText, int page, int size) {
        AiSearchFilter filter = geminiService.parseSearchQuery(queryText);
        if (filter == null) {
            return searchBills(null, null, null, null, page, size);
        }

        Pageable pageable = PageRequest.of(page, size, Sort.by("billDate").descending());
        
        Specification<Bill> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            
            if (filter.getCompanyName() != null && !filter.getCompanyName().isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("companyName")), "%" + filter.getCompanyName().toLowerCase().trim() + "%"));
            }

            if (filter.getVehicleType() != null && !filter.getVehicleType().isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("vehicleType")), "%" + filter.getVehicleType().toLowerCase().trim() + "%"));
            }
            
            if (filter.getMinAmount() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("grandTotal"), filter.getMinAmount()));
            }
            if (filter.getMaxAmount() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("grandTotal"), filter.getMaxAmount()));
            }

            if (filter.getMinKm() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("totalKms"), filter.getMinKm()));
            }
            if (filter.getMaxKm() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("totalKms"), filter.getMaxKm()));
            }
            
            if (filter.getDateFrom() != null && !filter.getDateFrom().isBlank()) {
                try {
                    LocalDate from = LocalDate.parse(filter.getDateFrom());
                    predicates.add(cb.greaterThanOrEqualTo(root.get("billDate"), from.atStartOfDay()));
                } catch (Exception e) {
                    log.warn("Failed to parse dateFrom: {}", filter.getDateFrom());
                }
            }
            
            if (filter.getDateTo() != null && !filter.getDateTo().isBlank()) {
                try {
                    LocalDate to = LocalDate.parse(filter.getDateTo());
                    predicates.add(cb.lessThanOrEqualTo(root.get("billDate"), to.atTime(23, 59, 59)));
                } catch (Exception e) {
                    log.warn("Failed to parse dateTo: {}", filter.getDateTo());
                }
            }

            if (filter.getKeywords() != null && !filter.getKeywords().isEmpty()) {
                for (String keyword : filter.getKeywords()) {
                    predicates.add(cb.or(
                        cb.like(cb.lower(root.get("notes")), "%" + keyword.toLowerCase() + "%"),
                        cb.like(cb.lower(root.get("billNumber")), "%" + keyword.toLowerCase() + "%")
                    ));
                }
            }
            
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        
        return billRepository.findAll(spec, pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public AiSearchFilter explainSearchNL(String queryText) {
        return geminiService.parseSearchQuery(queryText);
    }

    @Transactional(readOnly = true)
    public BillResponse getBillById(Long id) {
        Bill bill = billRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));
        return toResponse(bill);
    }

    private double calculateGrandTotal(BillRequest request) {
        double total = safeAmount(request.getBaseAmount());
        
        if (request.getDynamicCharges() != null) {
            total += request.getDynamicCharges().stream()
                    .mapToDouble(c -> safeAmount(c.getAmount()))
                    .sum();
        } else {
            // Fallback for requests without dynamic charges
            total += safeAmount(request.getDriverBata())
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
                
                if (name.contains("base")) bill.setBaseAmount(amount);
                else if (name.contains("bata") || name.contains("driver")) bill.setDriverBata(amount);
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
                bill.getPricingType(),
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
