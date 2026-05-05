package com.travelbilling.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiAssistantResponse {
    private String answer;
    private Double confidence;
    private List<String> references;
}
