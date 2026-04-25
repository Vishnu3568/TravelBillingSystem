package com.travelbilling.dto;

import java.util.List;

public record OwnerDashboardResponse(
        DashboardStats stats,
        List<RevenueTrend> revenueTrend,
        List<RecentBill> recentBills,
        List<UserActivity> recentUsersActivity) {

    public record DashboardStats(
            long todayBillsCount,
            double todayRevenue,
            double monthlyRevenue,
            double pendingPayments,
            long totalCompanies,
            long totalVehicles) {
    }

    public record RevenueTrend(
            String month,
            double revenue) {
    }

    public record RecentBill(
            Long id,
            String billNumber,
            String companyName,
            String vehicleRegistrationNumber,
            double amount,
            double paidAmount,
            double pendingAmount,
            String status,
            String billDate) {
    }

    public record UserActivity(
            Long id,
            String action,
            String performedBy,
            String actionTime) {
    }
}
