package com.travelbilling.dto;

import lombok.*;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class VehicleResponse {
    private Long id;
    private String registrationNumber;
    private String type;
    private String model;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
