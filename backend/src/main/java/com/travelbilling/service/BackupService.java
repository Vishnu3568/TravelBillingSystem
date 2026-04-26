package com.travelbilling.service;

import com.travelbilling.dto.BackupResponse;
import jakarta.annotation.PostConstruct;
import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
@Slf4j
@RequiredArgsConstructor
public class BackupService {

    private final AuditLogService auditLogService;

    @Value("${spring.datasource.username}")
    private String dbUser;

    @Value("${spring.datasource.password}")
    private String dbPass;

    @Value("${spring.datasource.url}")
    private String dbUrl;

    private final String backupDir = "backups";

    @PostConstruct
    public void init() {
        try {
            Files.createDirectories(Paths.get(backupDir));
        } catch (IOException e) {
            log.error("Could not create backup directory", e);
        }
    }

    public String createBackup() throws IOException, InterruptedException {
        String dbName = extractDbName(dbUrl);
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String fileName = "backup_" + timestamp + ".sql";
        Path path = Paths.get(backupDir, fileName);

        ProcessBuilder pb = new ProcessBuilder(
                "mysqldump",
                "-u" + dbUser,
                "-p" + dbPass,
                "--databases", dbName,
                "--result-file=" + path.toAbsolutePath().toString()
        );

        Process process = pb.start();
        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new IOException("Backup failed with exit code " + exitCode);
        }

        auditLogService.logAction("BACKUP_CREATED", "SYSTEM", "Database backup created: " + fileName);
        return fileName;
    }

    public void restoreBackup(MultipartFile file) throws IOException, InterruptedException {
        String dbName = extractDbName(dbUrl);
        Path tempFile = Files.createTempFile("restore_", ".sql");
        file.transferTo(tempFile);

        ProcessBuilder pb = new ProcessBuilder(
                "mysql",
                "-u" + dbUser,
                "-p" + dbPass,
                "-e", "source " + tempFile.toAbsolutePath().toString()
        );

        Process process = pb.start();
        int exitCode = process.waitFor();

        Files.deleteIfExists(tempFile);

        if (exitCode != 0) {
            throw new IOException("Restore failed with exit code " + exitCode);
        }
        
        auditLogService.logAction("RESTORE_DONE", "SYSTEM", "Database restoration completed successfully from uploaded file");
    }

    public List<BackupResponse> getHistory() {
        try {
            return Files.list(Paths.get(backupDir))
                    .filter(path -> path.toString().endsWith(".sql"))
                    .map(path -> {
                        try {
                            File file = path.toFile();
                            String name = file.getName();
                            long size = file.length();
                            LocalDateTime created = LocalDateTime.now(); // Fallback
                            // Try to parse timestamp from filename: backup_yyyyMMdd_HHmmss.sql
                            try {
                                String ts = name.substring(7, 22);
                                created = LocalDateTime.parse(ts, DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
                            } catch (Exception e) {}
                            
                            return new BackupResponse(name, size, created);
                        } catch (Exception e) {
                            return null;
                        }
                    })
                    .filter(r -> r != null)
                    .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            return Collections.emptyList();
        }
    }

    public byte[] getBackupFile(String fileName) throws IOException {
        Path path = Paths.get(backupDir, fileName);
        return Files.readAllBytes(path);
    }

    public void deleteBackup(String fileName) throws IOException {
        Path path = Paths.get(backupDir, fileName);
        Files.deleteIfExists(path);
        auditLogService.logAction("DELETE_BACKUP", "SYSTEM", "Backup file deleted: " + fileName);
    }

    @Scheduled(cron = "0 0 1 * * ?") // Daily at 1 AM
    public void autoBackup() {
        try {
            log.info("Starting automated daily backup...");
            createBackup();
        } catch (Exception e) {
            log.error("Automated backup failed", e);
        }
    }

    private String extractDbName(String url) {
        // jdbc:mysql://localhost:3306/travelbillingdb?...
        String clean = url.split("\\?")[0];
        return clean.substring(clean.lastIndexOf("/") + 1);
    }
}
