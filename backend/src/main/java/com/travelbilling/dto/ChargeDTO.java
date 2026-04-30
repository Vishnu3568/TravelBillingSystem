package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChargeDTO {
    private String name;
    private String calculation;
    private Double amount;
}
