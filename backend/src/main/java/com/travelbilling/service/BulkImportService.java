package com.travelbilling.service;

import com.travelbilling.dto.BillResponse;
import com.travelbilling.entity.Company;
import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.ai.service.GeminiService;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class BulkImportService {

    private final BillService billService;
    private final BillRepository billRepository;
    private final CompanyRepository companyRepository;
    private final DocxExtractionService docxExtractionService;
    private final GeminiService geminiService;

    @Transactional
    public Map<String, Object> importCompanies(MultipartFile[] files) {
        int successCount = 0;
        int failureCount = 0;
        List<String> errors = new ArrayList<>();

        for (MultipartFile file : files) {
            try {
                if (file.isEmpty()) continue;
                
                log.info("Starting AI-assisted company import for file: {}", file.getOriginalFilename());
                String rawText = docxExtractionService.extractRawText(file);
                List<Map<String, String>> companyData = geminiService.extractCompanies(rawText);

                for (Map<String, String> data : companyData) {
                    String name = data.get("name");
                    if (name == null || name.isBlank()) continue;

                    Optional<Company> existing = companyRepository.findByName(name.trim());
                    if (existing.isPresent()) {
                        Company e = existing.get();
                        if (data.get("address") != null && !data.get("address").isBlank()) e.setAddress(data.get("address"));
                        if (data.get("gstNumber") != null && !data.get("gstNumber").isBlank()) e.setGstNumber(data.get("gstNumber"));
                        companyRepository.save(e);
                    } else {
                        companyRepository.save(Company.builder()
                                .name(name.trim())
                                .address(data.get("address"))
                                .gstNumber(data.get("gstNumber"))
                                .build());
                    }
                    successCount++;
                }
            } catch (Exception e) {
                log.error("Company import failed for file: " + file.getOriginalFilename(), e);
                failureCount++;
                errors.add(file.getOriginalFilename() + ": " + e.getMessage());
            }
        }

        Map<String, Object> result = new HashMap<>();
        result.put("successCount", successCount);
        result.put("failureCount", failureCount);
        result.put("errors", errors);
        return result;
    }

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
                log.info("Starting AI-assisted bulk bill import for file: {}", fileName);
                
                String rawText = docxExtractionService.extractRawText(file);
                List<AiBillResponse> aiResponses = geminiService.parseBillText(rawText);
                
                if (aiResponses.isEmpty()) {
                    failureCount++;
                    errors.add(fileName + ": AI failed to extract any bills.");
                    continue;
                }
                
                List<BillResponse> savedList = billService.saveAiParsedBills(aiResponses, createdBy);
                
                if (savedList.isEmpty()) {
                    // Check if they were all duplicates
                    boolean allDuplicates = true;
                    for (AiBillResponse ai : aiResponses) {
                        String dsNo = ai.getDutySlipNo();
                        if (dsNo == null || dsNo.trim().isEmpty() || "---".equals(dsNo)) {
                            allDuplicates = false;
                            break;
                        }
                        if (!billRepository.existsByDutySlipNoAndCompanyName(dsNo, ai.getCompanyName())) {
                            allDuplicates = false;
                            break;
                        }
                    }
                    if (allDuplicates) {
                        duplicateCount += aiResponses.size();
                    } else {
                        failureCount++;
                        errors.add(fileName + ": Failed to save AI parsed bills.");
                    }
                } else {
                    successCount += savedList.size();
                    if (savedList.size() < aiResponses.size()) {
                        duplicateCount += (aiResponses.size() - savedList.size());
                    }
                }
                
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
}
