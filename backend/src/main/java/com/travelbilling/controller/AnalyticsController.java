package com.travelbilling.controller;

import com.travelbilling.ai.dto.AiInsightResponse;
import com.travelbilling.ai.dto.AiAssistantResponse;
import com.travelbilling.ai.dto.AiSuggestionRequest;
import com.travelbilling.ai.dto.AiSuggestionResponse;
import com.travelbilling.service.AnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;

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
            @RequestParam(required = false) Long billId,
            java.security.Principal principal) {
        return ResponseEntity.ok(analyticsService.askAssistant(query, billId, principal.getName()));
    }

    @PostMapping("/suggestions")
    @PreAuthorize("hasAnyRole('OWNER', 'MANAGER', 'OPERATOR')")
    public ResponseEntity<AiSuggestionResponse> getSuggestions(@RequestBody AiSuggestionRequest.CurrentBill currentBill) {
        return ResponseEntity.ok(analyticsService.generateSuggestions(currentBill));
    }
}
