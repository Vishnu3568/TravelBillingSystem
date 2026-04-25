package com.travelbilling.service;

import com.travelbilling.dto.OwnerDashboardResponse;
import com.travelbilling.entity.AuditLog;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.AuditLogRepository;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import com.travelbilling.repository.PaymentRepository;
import com.travelbilling.repository.VehicleRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.TextStyle;
import java.util.List;
import java.util.Locale;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DashboardService {
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ISO_LOCAL_DATE;
    private static final DateTimeFormatter DATE_TIME_FORMAT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    private final BillRepository billRepository;
    private final PaymentRepository paymentRepository;
    private final CompanyRepository companyRepository;
    private final VehicleRepository vehicleRepository;
    private final AuditLogRepository auditLogRepository;

    public OwnerDashboardResponse getOwnerDashboard() {
        LocalDate today = LocalDate.now();
        LocalDateTime todayStart = today.atStartOfDay();
        LocalDateTime tomorrowStart = today.plusDays(1).atStartOfDay();
        YearMonth currentMonth = YearMonth.from(today);
        LocalDateTime monthStart = currentMonth.atDay(1).atStartOfDay();
        LocalDateTime nextMonthStart = currentMonth.plusMonths(1).atDay(1).atStartOfDay();

        double totalBillAmount = safeAmount(billRepository.sumTotalBillAmount());
        double totalPaymentAmount = safeAmount(paymentRepository.sumTotalPaymentAmount());
        double pendingPayments = Math.max(0, totalBillAmount - totalPaymentAmount);

        OwnerDashboardResponse.DashboardStats stats = new OwnerDashboardResponse.DashboardStats(
                billRepository.countByBillDateGreaterThanEqualAndBillDateLessThan(todayStart, tomorrowStart),
                safeAmount(billRepository.sumAmountBetween(todayStart, tomorrowStart)),
                safeAmount(billRepository.sumAmountBetween(monthStart, nextMonthStart)),
                pendingPayments,
                companyRepository.count(),
                vehicleRepository.count());

        List<OwnerDashboardResponse.RecentBill> recentBills = billRepository
                .findAllByOrderByBillDateDesc(PageRequest.of(0, 5))
                .stream()
                .map(this::toRecentBill)
                .toList();

        List<OwnerDashboardResponse.UserActivity> activity = auditLogRepository
                .findAllByOrderByActionTimeDesc(PageRequest.of(0, 5))
                .stream()
                .map(this::toUserActivity)
                .toList();

        return new OwnerDashboardResponse(stats, getRevenueTrend(currentMonth), recentBills, activity);
    }

    private List<OwnerDashboardResponse.RevenueTrend> getRevenueTrend(YearMonth currentMonth) {
        return java.util.stream.IntStream.rangeClosed(0, 5)
                .mapToObj(monthOffset -> currentMonth.minusMonths(5L - monthOffset))
                .map(month -> new OwnerDashboardResponse.RevenueTrend(
                        month.getMonth().getDisplayName(TextStyle.SHORT, Locale.ENGLISH),
                        safeAmount(billRepository.sumAmountBetween(
                                month.atDay(1).atStartOfDay(),
                                month.plusMonths(1).atDay(1).atStartOfDay()))))
                .toList();
    }

    private OwnerDashboardResponse.RecentBill toRecentBill(Bill bill) {
        double amount = bill.getGrandTotal() == null
                ? safeAmount(bill.getAmount())
                : safeAmount(bill.getGrandTotal());
        double paidAmount = safeAmount(paymentRepository.sumAmountByBillId(bill.getId()));
        double pendingAmount = Math.max(0, amount - paidAmount);

        return new OwnerDashboardResponse.RecentBill(
                bill.getId(),
                valueOrFallback(bill.getBillNumber(), "BILL-" + bill.getId()),
                resolveCompanyName(bill),
                resolveVehicleName(bill),
                amount,
                paidAmount,
                pendingAmount,
                resolveBillStatus(bill, pendingAmount),
                bill.getBillDate() == null ? null : bill.getBillDate().toLocalDate().format(DATE_FORMAT));
    }

    private OwnerDashboardResponse.UserActivity toUserActivity(AuditLog auditLog) {
        LocalDateTime actionTime = auditLog.getActionTime() == null
                ? auditLog.getCreatedAt()
                : auditLog.getActionTime();

        return new OwnerDashboardResponse.UserActivity(
                auditLog.getId(),
                valueOrFallback(auditLog.getAction(), "Activity recorded"),
                valueOrFallback(auditLog.getPerformedBy(), "System"),
                actionTime == null ? null : actionTime.format(DATE_TIME_FORMAT));
    }

    private String resolveBillStatus(Bill bill, double pendingAmount) {
        if (pendingAmount <= 0) {
            return "Paid";
        }
        if (bill.getBillDate() != null && bill.getBillDate().toLocalDate().isBefore(LocalDate.now())) {
            return "Overdue";
        }
        return "Pending";
    }

    private String resolveCompanyName(Bill bill) {
        if (bill.getCompanyName() != null && !bill.getCompanyName().isBlank()) {
            return bill.getCompanyName();
        }
        return bill.getCompany() == null ? "Unassigned" : valueOrFallback(bill.getCompany().getName(), "Unnamed company");
    }

    private String resolveVehicleName(Bill bill) {
        if (bill.getVehicleName() != null && !bill.getVehicleName().isBlank()) {
            return bill.getVehicleName();
        }
        return bill.getVehicle() == null
                ? "Unassigned"
                : valueOrFallback(bill.getVehicle().getRegistrationNumber(), "Unnamed vehicle");
    }

    private double safeAmount(Double amount) {
        return amount == null ? 0 : amount;
    }

    private String valueOrFallback(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value;
    }
}
