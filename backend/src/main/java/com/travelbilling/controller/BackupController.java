package com.travelbilling.controller;

import com.travelbilling.dto.BackupResponse;
import com.travelbilling.service.BackupService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/backup")
@RequiredArgsConstructor
@PreAuthorize("hasRole('OWNER')")
public class BackupController {

    private final BackupService backupService;

    @PostMapping("/create")
    public ResponseEntity<String> createBackup() {
        try {
            String fileName = backupService.createBackup();
            return ResponseEntity.ok("Backup created successfully: " + fileName);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("Backup failed: " + e.getMessage());
        }
    }

    @PostMapping("/restore")
    public ResponseEntity<String> restoreBackup(@RequestParam("file") MultipartFile file) {
        try {
            backupService.restoreBackup(file);
            return ResponseEntity.ok("Database restored successfully");
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("Restore failed: " + e.getMessage());
        }
    }

    @GetMapping("/history")
    public ResponseEntity<List<BackupResponse>> getHistory() {
        return ResponseEntity.ok(backupService.getHistory());
    }

    @GetMapping("/download/{fileName}")
    public ResponseEntity<byte[]> downloadBackup(@PathVariable String fileName) {
        try {
            byte[] data = backupService.getBackupFile(fileName);
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + fileName)
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .body(data);
        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }

    @DeleteMapping("/{fileName}")
    public ResponseEntity<Void> deleteBackup(@PathVariable String fileName) {
        try {
            backupService.deleteBackup(fileName);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
