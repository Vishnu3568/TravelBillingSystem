package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class BackupResponse {
    private String fileName;
    private long fileSize;
    private LocalDateTime createdAt;
}
