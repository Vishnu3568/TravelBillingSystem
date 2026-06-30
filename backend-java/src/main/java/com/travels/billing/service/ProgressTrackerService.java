package com.travels.billing.service;

import lombok.Builder;
import lombok.Data;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ProgressTrackerService {

    @Data
    @Builder
    public static class ImportProgress {
        private String batchId;
        private String filename;
        private int totalPages;
        private int processedPages;
        private int successCount;
        private int failureCount;
        private boolean completed;
        private String status; // "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    }

    private final Map<String, ImportProgress> progressMap = new ConcurrentHashMap<>();

    public void initializeProgress(String batchId, String filename, int totalPages) {
        progressMap.put(batchId, ImportProgress.builder()
                .batchId(batchId)
                .filename(filename)
                .totalPages(totalPages)
                .processedPages(0)
                .successCount(0)
                .failureCount(0)
                .completed(false)
                .status("PROCESSING")
                .build());
    }

    public void updateProgress(String batchId, int processed, int success, int failure) {
        ImportProgress progress = progressMap.get(batchId);
        if (progress != null) {
            progress.setProcessedPages(processed);
            progress.setSuccessCount(success);
            progress.setFailureCount(failure);
            
            if (processed >= progress.getTotalPages()) {
                progress.setCompleted(true);
                progress.setStatus("COMPLETED");
            }
        }
    }

    public void setFailed(String batchId, String reason) {
        ImportProgress progress = progressMap.get(batchId);
        if (progress != null) {
            progress.setCompleted(true);
            progress.setStatus("FAILED: " + reason);
        }
    }

    public ImportProgress getProgress(String batchId) {
        return progressMap.get(batchId);
    }
}
