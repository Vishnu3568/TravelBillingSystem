package com.travelbilling.service;

import lombok.extern.slf4j.Slf4j;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFTable;
import org.apache.poi.xwpf.usermodel.XWPFTableCell;
import org.apache.poi.xwpf.usermodel.XWPFTableRow;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;

@Service
@Slf4j
public class DocxExtractionService {

    public String extractRawText(MultipartFile file) throws Exception {
        try (InputStream is = file.getInputStream(); XWPFDocument doc = new XWPFDocument(is)) {
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
