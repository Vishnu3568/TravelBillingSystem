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
                
                // Split text into chunks to avoid Gemini token limits and timeouts
                List<String> chunks = docxExtractionService.splitIntoChunks(rawText, 8000);
                log.info("Split document into {} chunks", chunks.size());

                for (int i = 0; i < chunks.size(); i++) {
                    log.info("Processing chunk {}/{}...", i + 1, chunks.size());
                    List<AiBillResponse> response = geminiService.parseBillText(chunks.get(i));
                    if (response != null) {
                        results.addAll(response);
                    }
                    
                    // Increase delay to 2 seconds to avoid aggressive rate limiting (429 errors)
                    if (chunks.size() > 1) {
                        Thread.sleep(2000); 
                    }
                }
            } catch (Exception e) {
                log.error("Failed to process file: {}", file.getOriginalFilename(), e);
                results.add(AiBillResponse.builder()
                        .warnings(List.of("Processing Error: " + e.getMessage()))
                        .build());
            }
        }

        return ResponseEntity.ok(results);
    }
}
