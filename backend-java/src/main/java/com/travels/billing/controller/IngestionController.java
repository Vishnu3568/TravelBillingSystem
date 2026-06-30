package com.travels.billing.controller;

import com.travels.billing.service.BatchProcessingService;
import com.travels.billing.service.ProgressTrackerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/ingest")
@CrossOrigin(origins = "*")
public class IngestionController {

    @Autowired
    private BatchProcessingService batchProcessingService;

    @Autowired
    private ProgressTrackerService progressTrackerService;

    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @RequestHeader(value = "X-User-Id", defaultValue = "system-owner") String userId
    ) {
        if (file.isEmpty()) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "File is empty");
            return ResponseEntity.badRequest().body(error);
        }

        String batchId = UUID.randomUUID().toString();
        String filename = file.getOriginalFilename();

        try {
            // Retrieve file input stream
            InputStream fileStream = file.getInputStream();

            // Trigger asynchronous processing
            batchProcessingService.processIngestionAsync(batchId, filename, fileStream, userId);

            Map<String, Object> response = new HashMap<>();
            response.put("batchId", batchId);
            response.put("filename", filename);
            response.put("status", "PROCESSING");
            response.put("message", "Document processing started asynchronously");
            
            return ResponseEntity.accepted().body(response);

        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to start document ingestion: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    @GetMapping("/progress/{batchId}")
    public ResponseEntity<ProgressTrackerService.ImportProgress> getProgress(@PathVariable("batchId") String batchId) {
        ProgressTrackerService.ImportProgress progress = progressTrackerService.getProgress(batchId);
        if (progress == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(progress);
    }
}
