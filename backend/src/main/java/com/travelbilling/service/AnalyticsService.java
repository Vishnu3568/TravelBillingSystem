package com.travelbilling.service;

import com.travelbilling.ai.dto.AiInsightResponse;
import com.travelbilling.ai.service.GeminiService;
import com.travelbilling.dto.DashboardStatsDTO;
import com.travelbilling.repository.BillRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AnalyticsService {

    private final BillRepository billRepository;
    private final GeminiService geminiService;

    @Transactional(readOnly = true)
    public AiInsightResponse getAiInsights() {
        DashboardStatsDTO stats = getDashboardStats();
        return geminiService.generateInsights(stats);
    }

    private DashboardStatsDTO getDashboardStats() {
        LocalDateTime sixMonthsAgo = LocalDateTime.now().minusMonths(6);
        
        Double totalRevenue = billRepository.sumTotalBillAmount();
        Long billCount = billRepository.count();
        
        List<DashboardStatsDTO.StatEntry> companyStats = billRepository.getCompanyRevenueStats().stream()
                .map(p -> new DashboardStatsDTO.StatEntry(p.getName(), p.getAmount(), p.getCount()))
                .collect(Collectors.toList());

        List<DashboardStatsDTO.StatEntry> vehicleStats = billRepository.getVehicleUsageStats().stream()
                .map(p -> new DashboardStatsDTO.StatEntry(p.getName(), p.getAmount(), p.getCount()))
                .collect(Collectors.toList());

        List<DashboardStatsDTO.StatEntry> monthlyRevenue = billRepository.getMonthlyRevenueStats(sixMonthsAgo).stream()
                .map(p -> new DashboardStatsDTO.StatEntry(p.getName(), p.getAmount(), p.getCount()))
                .collect(Collectors.toList());

        BillRepository.ChargeBreakdownProjection charges = billRepository.getChargeBreakdown();
        List<DashboardStatsDTO.StatEntry> chargeStats = new ArrayList<>();
        chargeStats.add(new DashboardStatsDTO.StatEntry("Driver Bata", charges.getBata(), null));
        chargeStats.add(new DashboardStatsDTO.StatEntry("Toll", charges.getToll(), null));
        chargeStats.add(new DashboardStatsDTO.StatEntry("Parking", charges.getParking(), null));
        chargeStats.add(new DashboardStatsDTO.StatEntry("Night Charges", charges.getNight(), null));
        chargeStats.add(new DashboardStatsDTO.StatEntry("Other", charges.getOther(), null));

        return DashboardStatsDTO.builder()
                .totalRevenue(totalRevenue)
                .billCount(billCount)
                .companyStats(companyStats)
                .vehicleStats(vehicleStats)
                .monthlyRevenue(monthlyRevenue)
                .chargeStats(chargeStats)
                .build();
    }
}
