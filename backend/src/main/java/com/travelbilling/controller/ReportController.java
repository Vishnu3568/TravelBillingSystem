package com.travelbilling.controller;

import com.travelbilling.dto.ReportSummaryResponse;
import com.travelbilling.dto.TopEntityResponse;
import com.travelbilling.service.ReportService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/reports")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @GetMapping("/summary")
    public ResponseEntity<ReportSummaryResponse> getSummary() {
        return ResponseEntity.ok(reportService.getSummary());
    }

    @GetMapping("/top-companies")
    public ResponseEntity<List<TopEntityResponse>> getTopCompanies() {
        return ResponseEntity.ok(reportService.getTopCompanies());
    }

    @GetMapping("/top-vehicles")
    public ResponseEntity<List<TopEntityResponse>> getTopVehicles() {
        return ResponseEntity.ok(reportService.getTopVehicles());
    }
}
