package com.travelbilling.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
@Table(name = "bills")
public class Bill {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String billNumber;
    private Double amount;
    private LocalDateTime billDate;
    private String companyName;
    private String vehicleName;
    private String dutySlipNo;
    private LocalDateTime tripDate;
    private String vehicleType;
    private String acNonAc;
    private Double totalKms;
    private Double totalHours;
    private Double extraKms;
    private Double extraHours;
    private String tripType;
    private Double baseAmount;
    private Double driverBata;
    private Double parking;
    private Double toll;
    private Double nightCharges;
    private Double otherCharges;

    @Column(length = 1000)
    private String notes;

    @Column(columnDefinition = "TEXT")
    private String dynamicCharges;

    private String contactPerson;
    private String bookedBy;
    private String managerName;

    private Double grandTotal;
    private String createdBy;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @ManyToOne
    @JoinColumn(name = "vehicle_id")
    private Vehicle vehicle;

    @OneToMany(mappedBy = "bill")
    private List<Payment> payments;

    @PrePersist
    protected void onCreate() {
        createdAt = updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
