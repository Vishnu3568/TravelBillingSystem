package com.travelbilling.controller;

import com.travelbilling.service.BulkImportService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/import")
@RequiredArgsConstructor
public class BulkImportController {

    private final BulkImportService bulkImportService;

    @PostMapping("/bills")
    public ResponseEntity<?> importBills(
            @RequestParam("files") MultipartFile[] files,
            Authentication authentication) {
        
        String username = authentication != null ? authentication.getName() : "anonymous";
        Map<String, Object> summary = bulkImportService.importBills(files, username);
        
        return ResponseEntity.ok(summary);
    }

    @PostMapping("/companies")
    public ResponseEntity<?> importCompanies(@RequestParam("files") MultipartFile[] files) {
        Map<String, Object> summary = bulkImportService.importCompanies(files);
        return ResponseEntity.ok(summary);
    }
}
