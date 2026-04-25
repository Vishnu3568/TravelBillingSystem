package com.travelbilling.controller;

import com.travelbilling.dto.OwnerDashboardResponse;
import com.travelbilling.service.DashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {
    private final DashboardService dashboardService;

    @GetMapping("/owner")
    @PreAuthorize("hasRole('OWNER')")
    public OwnerDashboardResponse getOwnerDashboard() {
        return dashboardService.getOwnerDashboard();
    }
}
