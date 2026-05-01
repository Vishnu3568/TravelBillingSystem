package com.travelbilling.service;

import com.travelbilling.dto.BillRequest;
import com.travelbilling.dto.ChargeDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.entity.Company;
import com.travelbilling.entity.Vehicle;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import com.travelbilling.repository.VehicleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.xwpf.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
@Slf4j
public class BulkImportService {

    private final BillService billService;
    private final BillRepository billRepository;
    private final CompanyRepository companyRepository;
    private final VehicleRepository vehicleRepository;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("dd-MM-yyyy");

    @Transactional
    public Map<String, Object> importBills(MultipartFile[] files, String createdBy) {
        int successCount = 0;
        int duplicateCount = 0;
        int failureCount = 0;
        List<String> errors = new ArrayList<>();

        for (MultipartFile file : files) {
            try {
                if (file.isEmpty()) continue;
                
                String fileName = file.getOriginalFilename();
                BillRequest request = parseDocx(file);
                
                if (request == null) {
                    failureCount++;
                    errors.add(fileName + ": Failed to parse content");
                    continue;
                }

                // Handle Duplicates based on Duty Slip + Company
                if (billRepository.existsByDutySlipNoAndCompanyName(request.getDutySlipNo(), request.getCompanyName())) {
                    duplicateCount++;
                    continue;
                }

                // Ensure Company exists
                findOrCreateCompany(request.getCompanyName(), request.getNotes()); // Using notes as temp address if found

                // Ensure Vehicle exists
                findOrCreateVehicle(request.getVehicleName(), request.getVehicleType());

                // Create Bill
                billService.createBill(request, createdBy);
                successCount++;

            } catch (Exception e) {
                log.error("Import failed for file: " + file.getOriginalFilename(), e);
                failureCount++;
                errors.add(file.getOriginalFilename() + ": " + e.getMessage());
            }
        }

        Map<String, Object> result = new HashMap<>();
        result.put("successCount", successCount);
        result.put("duplicateCount", duplicateCount);
        result.put("failureCount", failureCount);
        result.put("errors", errors);
        return result;
    }

    private BillRequest parseDocx(MultipartFile file) throws Exception {
        try (InputStream is = file.getInputStream(); XWPFDocument doc = new XWPFDocument(is)) {
            BillRequest request = new BillRequest();
            request.setDynamicCharges(new ArrayList<>());
            
            StringBuilder fullText = new StringBuilder();
            for (XWPFParagraph p : doc.getParagraphs()) {
                fullText.append(p.getText()).append("\n");
            }

            // Extract Header Info
            String text = fullText.toString();
            request.setBillDate(parseDate(extractValue(text, "Date:\\s*(\\d{2}-\\d{2}-\\d{4})")));
            request.setCompanyName(extractValue(text, "To\\.?\\s*(.*)"));
            
            if (request.getCompanyName() == null) {
                 request.setCompanyName("Unknown Company");
            }

            // Table Parsing
            for (XWPFTable table : doc.getTables()) {
                for (XWPFTableRow row : table.getRows()) {
                    List<XWPFTableCell> cells = row.getTableCells();
                    if (cells.size() < 4) continue;

                    String firstCell = cells.get(0).getText().trim();
                    
                    // Look for the main data row (Slip No, Date, Vehicle, etc.)
                    if (isNumeric(firstCell)) {
                        request.setDutySlipNo(firstCell);
                        request.setTripDate(parseDate(cells.get(1).getText().trim()));
                        request.setVehicleName(cells.get(2).getText().trim());
                        request.setTotalKms(parseDouble(cells.get(3).getText()));
                        
                        if (cells.size() >= 5) request.setTotalHours(parseDouble(cells.get(4).getText()));
                        if (cells.size() >= 6) request.setExtraKms(parseDouble(cells.get(5).getText()));
                        if (cells.size() >= 7) request.setExtraHours(parseDouble(cells.get(6).getText()));
                    }

                    // Look for Charges
                    String rowText = row.getTableCells().stream().map(XWPFTableCell::getText).reduce("", (a, b) -> a + " " + b).toLowerCase();
                    if (rowText.contains("base amount") || rowText.contains("total amount")) {
                         addCharge(request, "Base Amount", parseDouble(cells.get(cells.size()-1).getText()));
                    } else if (rowText.contains("driver bata")) {
                         addCharge(request, "Driver Bata", parseDouble(cells.get(cells.size()-1).getText()));
                    } else if (rowText.contains("toll")) {
                         addCharge(request, "Toll", parseDouble(cells.get(cells.size()-1).getText()));
                    } else if (rowText.contains("parking")) {
                         addCharge(request, "Parking", parseDouble(cells.get(cells.size()-1).getText()));
                    }
                }
            }

            // Defaults if missing
            if (request.getBillDate() == null) request.setBillDate(LocalDate.now());
            if (request.getDutySlipNo() == null) request.setDutySlipNo("IMP-" + System.currentTimeMillis());
            if (request.getVehicleName() == null) request.setVehicleName("Unknown Vehicle");
            request.setPricingType("BASE");
            request.setTripType("Local");

            return request;
        }
    }

    private void addCharge(BillRequest request, String name, Double amount) {
        if (amount != null && amount > 0) {
            request.getDynamicCharges().add(new ChargeDTO(name, "Manual", amount));
        }
    }

    private void findOrCreateCompany(String name, String address) {
        if (name == null || name.isBlank()) return;
        companyRepository.findByName(name.trim()).orElseGet(() -> {
            Company company = Company.builder()
                    .name(name.trim())
                    .address(address != null ? address : "")
                    .build();
            return companyRepository.save(company);
        });
    }

    private void findOrCreateVehicle(String regNo, String type) {
        if (regNo == null || regNo.isBlank()) return;
        vehicleRepository.findByRegistrationNumber(regNo.trim()).orElseGet(() -> {
            Vehicle vehicle = Vehicle.builder()
                    .registrationNumber(regNo.trim())
                    .type(type != null ? type : "Car")
                    .model("Imported")
                    .build();
            return vehicleRepository.save(vehicle);
        });
    }

    private String extractValue(String text, String regex) {
        Pattern pattern = Pattern.compile(regex, Pattern.CASE_INSENSITIVE);
        Matcher matcher = pattern.matcher(text);
        if (matcher.find()) return matcher.group(1).trim();
        return null;
    }

    private LocalDate parseDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) return null;
        try {
            return LocalDate.parse(dateStr, DATE_FORMATTER);
        } catch (Exception e) {
            return null;
        }
    }

    private Double parseDouble(String val) {
        if (val == null) return 0.0;
        try {
            return Double.parseDouble(val.replaceAll("[^\\d\\.]", ""));
        } catch (Exception e) {
            return 0.0;
        }
    }

    private boolean isNumeric(String str) {
        return str != null && str.matches("\\d+");
    }
}
