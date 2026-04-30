package com.travelbilling.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import java.util.List;
import lombok.Data;

@Data
public class BillRequest {
    @NotNull
    private LocalDate billDate;

    @NotBlank
    @Size(max = 150)
    private String companyName;

    @NotBlank
    @Size(max = 150)
    private String vehicleName;

    @NotBlank
    @Size(max = 100)
    private String dutySlipNo;

    private LocalDate tripDate;
    private String vehicleType;
    private String acNonAc;

    @DecimalMin(value = "0.0")
    private Double totalKms = 0.0;

    @DecimalMin(value = "0.0")
    private Double totalHours = 0.0;

    @DecimalMin(value = "0.0")
    private Double extraKms = 0.0;

    @DecimalMin(value = "0.0")
    private Double extraHours = 0.0;

    private String tripType;

    @DecimalMin(value = "0.0")
    private Double baseAmount = 0.0;

    @DecimalMin(value = "0.0")
    private Double driverBata = 0.0;

    @DecimalMin(value = "0.0")
    private Double parking = 0.0;

    @DecimalMin(value = "0.0")
    private Double toll = 0.0;

    @DecimalMin(value = "0.0")
    private Double nightCharges = 0.0;

    @DecimalMin(value = "0.0")
    private Double otherCharges = 0.0;

    private List<ChargeDTO> dynamicCharges;

    @Size(max = 1000)
    private String notes;

    private String contactPerson;
    private String bookedBy;
    private String managerName;
}
