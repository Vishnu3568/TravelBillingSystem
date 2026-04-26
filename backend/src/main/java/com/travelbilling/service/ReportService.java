package com.travelbilling.service;

import com.travelbilling.dto.ReportSummaryResponse;
import com.travelbilling.dto.TopEntityResponse;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import com.travelbilling.repository.VehicleRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.List;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ReportService {

    private final BillRepository billRepository;
    private final CompanyRepository companyRepository;
    private final VehicleRepository vehicleRepository;

    public ReportSummaryResponse getSummary() {
        LocalDate today = LocalDate.now();
        LocalDateTime todayStart = today.atStartOfDay();
        LocalDateTime tomorrowStart = today.plusDays(1).atStartOfDay();
        YearMonth currentMonth = YearMonth.from(today);
        LocalDateTime monthStart = currentMonth.atDay(1).atStartOfDay();
        LocalDateTime nextMonthStart = currentMonth.plusMonths(1).atDay(1).atStartOfDay();

        return new ReportSummaryResponse(
                billRepository.countByBillDateGreaterThanEqualAndBillDateLessThan(todayStart, tomorrowStart),
                safeAmount(billRepository.sumAmountBetween(todayStart, tomorrowStart)),
                billRepository.countByBillDateGreaterThanEqualAndBillDateLessThan(monthStart, nextMonthStart),
                safeAmount(billRepository.sumAmountBetween(monthStart, nextMonthStart)),
                billRepository.count(),
                companyRepository.count(),
                vehicleRepository.count());
    }

    public List<TopEntityResponse> getTopCompanies() {
        return billRepository.findTopCompanies(PageRequest.of(0, 5))
                .stream()
                .map(p -> new TopEntityResponse(p.getName(), safeAmount(p.getRevenue())))
                .collect(Collectors.toList());
    }

    public List<TopEntityResponse> getTopVehicles() {
        return billRepository.findTopVehicles(PageRequest.of(0, 5))
                .stream()
                .map(p -> new TopEntityResponse(p.getName(), safeAmount(p.getRevenue())))
                .collect(Collectors.toList());
    }

    private double safeAmount(Double amount) {
        return amount == null ? 0 : amount;
    }
}
