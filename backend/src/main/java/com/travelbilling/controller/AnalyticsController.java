package com.travelbilling.controller;

import com.travelbilling.ai.dto.AiInsightResponse;
import com.travelbilling.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.CrossOrigin;

@RestController
@RequestMapping("/api/analytics")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/ai-insights")
    public ResponseEntity<AiInsightResponse> getAiInsights() {
        return ResponseEntity.ok(analyticsService.getAiInsights());
    }
}
