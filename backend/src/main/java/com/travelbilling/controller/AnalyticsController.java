package com.travelbilling.controller;

import com.travelbilling.ai.dto.AiInsightResponse;
import com.travelbilling.ai.dto.AiAssistantResponse;
import com.travelbilling.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;
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

    @PostMapping("/assistant")
    @PreAuthorize("hasAnyRole('OWNER', 'MANAGER')")
    public ResponseEntity<AiAssistantResponse> askAssistant(
            @RequestParam String query,
            @RequestParam(required = false) Long billId) {
        return ResponseEntity.ok(analyticsService.askAssistant(query, billId));
    }
}
