package com.travelbilling.dto;

import lombok.*;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CompanyResponse {
    private Long id;
    private String name;
    private String address;
    private String gstNumber;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
