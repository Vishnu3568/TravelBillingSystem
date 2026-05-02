package com.travelbilling.service;

import lombok.extern.slf4j.Slf4j;
import org.apache.poi.hwpf.extractor.WordExtractor;
import org.apache.poi.xwpf.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

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
}
