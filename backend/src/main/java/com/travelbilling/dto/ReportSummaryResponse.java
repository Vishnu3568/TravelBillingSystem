package com.travelbilling.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ReportSummaryResponse {
    private long todayBillsCount;
    private double todayRevenue;
    private long monthlyBillsCount;
    private double monthlyRevenue;
    private long totalBills;
    private long totalCompanies;
    private long totalVehicles;
}
