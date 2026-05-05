package com.travelbilling.service;

import com.travelbilling.ai.dto.AiInsightResponse;
import com.travelbilling.ai.dto.AiAssistantRequest;
import com.travelbilling.ai.dto.AiAssistantResponse;
import com.travelbilling.ai.service.GeminiService;
import com.travelbilling.dto.DashboardStatsDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.repository.CompanyRepository;
import com.travelbilling.repository.VehicleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class AnalyticsService {

    private final BillRepository billRepository;
    private final CompanyRepository companyRepository;
    private final VehicleRepository vehicleRepository;
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

    @Transactional(readOnly = true)
    public AiAssistantResponse askAssistant(String query, Long billId) {
        AiAssistantRequest.AiAssistantRequestBuilder requestBuilder = AiAssistantRequest.builder()
                .userQuery(query);

        if (billId != null) {
            Bill bill = billRepository.findById(billId).orElse(null);
            if (bill != null) {
                requestBuilder.contextType("BILL");
                requestBuilder.billData(AiAssistantRequest.BillData.builder()
                        .billNumber(bill.getBillNumber())
                        .companyName(bill.getCompanyName())
                        .totalKm(bill.getTotalKms())
                        .totalHours(bill.getTotalHours())
                        .totalAmount(bill.getGrandTotal())
                        .charges(parseCharges(bill.getDynamicCharges()))
                        .build());
            } else {
                requestBuilder.contextType("GLOBAL");
            }
        } else {
            requestBuilder.contextType("GLOBAL");
        }

        if (requestBuilder.build().getContextType().equals("GLOBAL")) {
            DashboardStatsDTO stats = getDashboardStats();
            Double revenue = stats.getTotalRevenue();
            requestBuilder.aggregatedData(AiAssistantRequest.AggregatedData.builder()
                    .totalRevenue(revenue)
                    .companyCount(companyRepository.count())
                    .vehicleCount(vehicleRepository.count())
                    .topCompanies(stats.getCompanyStats().stream()
                            .limit(5)
                            .map(s -> {
                                Map<String, Object> m = new HashMap<>();
                                m.put("name", s.getName());
                                m.put("revenue", s.getAmount());
                                return m;
                            })
                            .collect(Collectors.toList()))
                    .recentBills(billRepository.findTop5ByOrderByCreatedAtDesc().stream()
                            .map(b -> {
                                Map<String, Object> m = new HashMap<>();
                                m.put("number", b.getBillNumber());
                                m.put("company", b.getCompanyName());
                                m.put("total", b.getGrandTotal());
                                return m;
                            })
                            .collect(Collectors.toList()))
                    .build());
        }

        return geminiService.askAssistant(requestBuilder.build());
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> parseCharges(String chargesJson) {
        if (chargesJson == null) return List.of();
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper().readValue(chargesJson, List.class);
        } catch (Exception e) {
            return List.of();
        }
    }
}
