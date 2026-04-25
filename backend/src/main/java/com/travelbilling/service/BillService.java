package com.travelbilling.service;

import com.travelbilling.dto.BillRequest;
import com.travelbilling.dto.BillResponse;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.BillRepository;
import java.security.SecureRandom;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class BillService {
    private static final DateTimeFormatter BILL_NUMBER_DATE = DateTimeFormatter.BASIC_ISO_DATE;
    private static final SecureRandom RANDOM = new SecureRandom();

    private final BillRepository billRepository;

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
                .totalKms(safeAmount(request.getTotalKms()))
                .totalHours(safeAmount(request.getTotalHours()))
                .baseAmount(safeAmount(request.getBaseAmount()))
                .driverBata(safeAmount(request.getDriverBata()))
                .parking(safeAmount(request.getParking()))
                .toll(safeAmount(request.getToll()))
                .nightCharges(safeAmount(request.getNightCharges()))
                .otherCharges(safeAmount(request.getOtherCharges()))
                .notes(request.getNotes())
                .grandTotal(grandTotal)
                .createdBy(createdBy)
                .build();

        return toResponse(billRepository.save(bill));
    }

    @Transactional(readOnly = true)
    public List<BillResponse> getBills() {
        return billRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public BillResponse getBillById(Long id) {
        Bill bill = billRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));
        return toResponse(bill);
    }

    private double calculateGrandTotal(BillRequest request) {
        return safeAmount(request.getBaseAmount())
                + safeAmount(request.getDriverBata())
                + safeAmount(request.getParking())
                + safeAmount(request.getToll())
                + safeAmount(request.getNightCharges())
                + safeAmount(request.getOtherCharges());
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
                safeAmount(bill.getTotalKms()),
                safeAmount(bill.getTotalHours()),
                safeAmount(bill.getBaseAmount()),
                safeAmount(bill.getDriverBata()),
                safeAmount(bill.getParking()),
                safeAmount(bill.getToll()),
                safeAmount(bill.getNightCharges()),
                safeAmount(bill.getOtherCharges()),
                bill.getNotes(),
                safeAmount(bill.getGrandTotal()),
                bill.getCreatedBy(),
                bill.getCreatedAt());
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
}
