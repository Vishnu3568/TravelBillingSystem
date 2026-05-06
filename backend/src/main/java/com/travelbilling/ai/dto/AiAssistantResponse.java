package com.travelbilling.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiAssistantResponse {
    private String answer;
    private Double confidence;
    private List<String> references;
    private ActionData action;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ActionData {
        private String type; // CREATE_BILL | DELETE_BILL
        private Map<String, Object> data;
    }
}
