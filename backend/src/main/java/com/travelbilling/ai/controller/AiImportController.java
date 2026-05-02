package com.travelbilling.ai.controller;

import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.ai.service.GeminiService;
import com.travelbilling.service.DocxExtractionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/import/ai-parse")
@RequiredArgsConstructor
@Slf4j
@CrossOrigin(origins = "*")
public class AiImportController {

    private final GeminiService geminiService;
    private final DocxExtractionService docxExtractionService;

    @PostMapping
    public ResponseEntity<List<AiBillResponse>> parseBills(@RequestParam("files") MultipartFile[] files) {
        List<AiBillResponse> results = new ArrayList<>();

        for (MultipartFile file : files) {
            try {
                log.info("AI Parsing file: {}", file.getOriginalFilename());
                String rawText = docxExtractionService.extractRawText(file);
                AiBillResponse response = geminiService.parseBillText(rawText);
                if (response != null) {
                    // Set file name as a reference if needed or in warnings
                    if (response.getWarnings() == null) response.setWarnings(new ArrayList<>());
                    results.add(response);
                }
            } catch (Exception e) {
                log.error("Failed to extract text from file: {}", file.getOriginalFilename(), e);
                results.add(AiBillResponse.builder()
                        .warnings(List.of("Extraction Error: " + e.getMessage()))
                        .build());
            }
        }

        return ResponseEntity.ok(results);
    }
}
