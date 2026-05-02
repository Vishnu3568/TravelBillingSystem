package com.travelbilling.service;

import lombok.extern.slf4j.Slf4j;
import org.apache.poi.hwpf.extractor.WordExtractor;
import org.apache.poi.xwpf.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import java.util.ArrayList;
import java.util.List;

import java.io.InputStream;

@Service
@Slf4j
public class DocxExtractionService {

    public String extractRawText(MultipartFile file) throws Exception {
        String fileName = file.getOriginalFilename() != null ? file.getOriginalFilename().toLowerCase() : "";
        
        try (InputStream is = file.getInputStream()) {
            if (fileName.endsWith(".doc")) {
                log.info("Extracting legacy .doc file");
                try (WordExtractor extractor = new WordExtractor(is)) {
                    return extractor.getText();
                }
            } else {
                log.info("Extracting modern .docx file");
                try (XWPFDocument doc = new XWPFDocument(is)) {
                    StringBuilder fullText = new StringBuilder();
                    
                    // Extract Paragraphs
                    for (XWPFParagraph p : doc.getParagraphs()) {
                        fullText.append(p.getText()).append("\n");
                    }

                    // Extract Tables
                    for (XWPFTable table : doc.getTables()) {
                        for (XWPFTableRow row : table.getRows()) {
                            for (XWPFTableCell cell : row.getTableCells()) {
                                fullText.append(cell.getText()).append("\t");
                            }
                            fullText.append("\n");
                        }
                        fullText.append("\n");
                    }
                    return fullText.toString();
                }
            }
        }
    }

    public List<String> splitIntoChunks(String text, int chunkSize) {
        List<String> chunks = new ArrayList<>();
        if (text == null || text.isBlank()) return chunks;

        int currentPos = 0;
        while (currentPos < text.length()) {
            int end = Math.min(currentPos + chunkSize, text.length());
            
            // Try to find a good breaking point (like a newline) near the end of the chunk
            if (end < text.length()) {
                int lastNewline = text.lastIndexOf("\n", end);
                if (lastNewline > currentPos) {
                    end = lastNewline;
                }
            }
            
            chunks.add(text.substring(currentPos, end).trim());
            currentPos = end;
            
            // Prevent infinite loop if something goes wrong
            if (chunks.size() > 100) break; 
        }
        return chunks;
    }
}
