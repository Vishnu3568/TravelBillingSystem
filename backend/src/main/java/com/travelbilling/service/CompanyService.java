package com.travelbilling.service;

import com.travelbilling.dto.CompanyRequest;
import com.travelbilling.dto.CompanyResponse;
import com.travelbilling.entity.Company;
import com.travelbilling.repository.CompanyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CompanyService {

    private final CompanyRepository companyRepository;
    private final AuditLogService auditLogService;

    public List<CompanyResponse> getAllCompanies() {
        return companyRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional
    public CompanyResponse createCompany(CompanyRequest request) {
        Company company = Company.builder()
                .name(request.getName())
                .address(request.getAddress())
                .gstNumber(request.getHasGst() != null && request.getHasGst() ? request.getGstNumber() : null)
                .build();
        Company saved = companyRepository.save(company);
        auditLogService.logAction("CREATE_COMPANY", "COMPANY", "Created company: " + saved.getName());
        return mapToResponse(saved);
    }

    @Transactional
    public CompanyResponse updateCompany(Long id, CompanyRequest request) {
        Company company = companyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Company not found"));
        
        company.setName(request.getName());
        company.setAddress(request.getAddress());
        company.setGstNumber(request.getHasGst() != null && request.getHasGst() ? request.getGstNumber() : null);
        
        Company saved = companyRepository.save(company);
        auditLogService.logAction("UPDATE_COMPANY", "COMPANY", "Updated company: " + saved.getName());
        return mapToResponse(saved);
    }

    @Transactional
    public void deleteCompany(Long id) {
        Company company = companyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Company not found"));
        String name = company.getName();
        companyRepository.delete(company);
        auditLogService.logAction("DELETE_COMPANY", "COMPANY", "Deleted company: " + name);
    }

    private CompanyResponse mapToResponse(Company company) {
        return CompanyResponse.builder()
                .id(company.getId())
                .name(company.getName())
                .address(company.getAddress())
                .gstNumber(company.getGstNumber())
                .createdAt(company.getCreatedAt())
                .updatedAt(company.getUpdatedAt())
                .build();
    }
}
