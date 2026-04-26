package com.travelbilling.dto;

import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class VehicleRequest {
    private String registrationNumber;
    private String type;
    private String model;
}
