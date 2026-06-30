package com.travels.billing.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "bills")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ParsedBill {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "bill_number", unique = true, nullable = false)
    private String billNumber;

    @Column(name = "bill_date")
    private LocalDateTime billDate;

    @Column(name = "company_name")
    private String companyName;

    @Column(name = "vehicle_name")
    private String vehicleName;

    @Column(name = "duty_slip_no")
    private String dutySlipNo;

    @Column(name = "trip_date")
    private LocalDate tripDate;

    @Column(name = "vehicle_type")
    private String vehicleType;

    @Column(name = "ac_non_ac")
    private String acNonAc;

    @Column(name = "total_kms")
    private Double totalKms;

    @Column(name = "total_hours")
    private Double totalHours;

    @Column(name = "extra_kms")
    private Double extraKms;

    @Column(name = "extra_hours")
    private Double extraHours;

    @Column(name = "trip_type")
    private String tripType;

    @Column(name = "pricing_type")
    private String pricingType;

    @Column(name = "base_amount")
    private Double baseAmount;

    @Column(name = "driver_bata")
    private Double driverBata;

    @Column(name = "night_charges")
    private Double nightCharges;

    @Column(name = "other_charges")
    private Double otherCharges;

    @Column(name = "notes", length = 1000)
    private String notes;

    @Column(name = "dynamic_charges", columnDefinition = "TEXT")
    private String dynamicCharges;

    @Column(name = "contact_person")
    private String contactPerson;

    @Column(name = "booked_by")
    private String bookedBy;

    @Column(name = "manager_name")
    private String managerName;

    @Column(name = "grand_total")
    private Double grandTotal;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
