package com.travels.billing.service;

import com.travels.billing.model.BillChunk;
import org.apache.poi.xwpf.usermodel.*;
import org.openxmlformats.schemas.wordprocessingml.x2006.main.CTBr;
import org.openxmlformats.schemas.wordprocessingml.x2006.main.CTR;
import org.openxmlformats.schemas.wordprocessingml.x2006.main.STBrType;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.*;

@Service
public class DocumentAnalyzerService {

    public List<BillChunk> analyzeAndSplitDocument(InputStream inputStream, String filename) throws Exception {
        List<BillChunk> chunks = new ArrayList<>();
        
        try (XWPFDocument document = new XWPFDocument(inputStream)) {
            int currentPage = 1;
            StringBuilder textBuffer = new StringBuilder();
            List<List<String>> tableBuffer = new ArrayList<>();
            
            // Loop through body elements in layout order
            for (IBodyElement element : document.getBodyElements()) {
                if (element.getElementType() == BodyElementType.PARAGRAPH) {
                    XWPFParagraph paragraph = (XWPFParagraph) element;
                    boolean hasPageBreak = checkForPageBreak(paragraph);
                    
                    if (hasPageBreak && textBuffer.length() > 0) {
                        // Package current page buffer as a chunk
                        chunks.add(buildChunk(filename, currentPage, textBuffer, tableBuffer));
                        currentPage++;
                        
                        // Reset buffers for the next page
                        textBuffer = new StringBuilder();
                        tableBuffer = new ArrayList<>();
                    }
                    
                    String pText = paragraph.getText();
                    if (pText != null && !pText.trim().isEmpty()) {
                        textBuffer.append(pText).append("\n");
                    }
                    
                } else if (element.getElementType() == BodyElementType.TABLE) {
                    XWPFTable table = (XWPFTable) element;
                    List<List<String>> extractedTable = extractTableData(table);
                    tableBuffer.addAll(extractedTable);
                    
                    // Also append table content as formatted text to the text buffer
                    for (List<String> row : extractedTable) {
                        textBuffer.append(String.join(" | ", row)).append("\n");
                    }
                }
            }
            
            // Package final remaining buffer
            if (textBuffer.length() > 0 || !tableBuffer.isEmpty()) {
                chunks.add(buildChunk(filename, currentPage, textBuffer, tableBuffer));
            }
        }
        
        // Fallback: If no page breaks were found, split by major headers (e.g. "Duty Slip", "Bill No")
        if (chunks.size() == 1) {
            chunks = fallbackSplit(chunks.get(0), filename);
        }
        
        return chunks;
    }

    private boolean checkForPageBreak(XWPFParagraph paragraph) {
        if (paragraph == null) return false;
        
        // 1. Check paragraph properties for pageBreakBefore
        if (paragraph.isPageBreak()) {
            return true;
        }
        
        // 2. Check run-level page break XML elements
        for (XWPFRun run : paragraph.getRuns()) {
            CTR ctr = run.getCTR();
            if (ctr == null) continue;
            
            // Check explicit break elements
            for (CTBr br : ctr.getBrList()) {
                if (br.getType() == STBrType.PAGE) {
                    return true;
                }
            }
            
            // Check lastRenderedPageBreak tag
            if (ctr.toString().contains("lastRenderedPageBreak")) {
                return true;
            }
        }
        return false;
    }

    private List<List<String>> extractTableData(XWPFTable table) {
        List<List<String>> tableData = new ArrayList<>();
        for (XWPFTableRow row : table.getRows()) {
            List<String> rowData = new ArrayList<>();
            for (XWPFTableCell cell : row.getTableCells()) {
                rowData.add(cell.getText().trim());
            }
            tableData.add(rowData);
        }
        return tableData;
    }

    private BillChunk buildChunk(String filename, int pageNum, StringBuilder text, List<List<String>> tables) {
        Map<String, Object> documentMetadata = new HashMap<>();
        documentMetadata.put("filename", filename);
        documentMetadata.put("timestamp", new Date());
        
        Map<String, Object> layoutMetadata = new HashMap<>();
        layoutMetadata.put("tablesCount", tables.size());
        layoutMetadata.put("charactersCount", text.length());
        
        return BillChunk.builder()
                .companyName(extractCompanyNameFromText(text.toString()))
                .pageNumber(pageNum)
                .extractedText(text.toString())
                .extractedTables(tables)
                .documentMetadata(documentMetadata)
                .layoutMetadata(layoutMetadata)
                .build();
    }

    private String extractCompanyNameFromText(String text) {
        // Look for common patterns, fallback to default
        if (text.contains("Sri Tulja Bhavani")) {
            return "Sri Tulja Bhavani Travels";
        }
        // Match first line or key business markers
        String[] lines = text.split("\n");
        if (lines.length > 0 && lines[0].length() < 100) {
            return lines[0].trim();
        }
        return "Unknown Company";
    }

    private List<BillChunk> fallbackSplit(BillChunk singleChunk, String filename) {
        // If no hard XML page breaks exist, look for recurring structural markers
        String text = singleChunk.getExtractedText();
        String[] billsText = text.split("(?i)(?=duty\\s+slip|bill\\s+no|invoice\\s+no)");
        
        if (billsText.length <= 1) {
            return Collections.singletonList(singleChunk);
        }
        
        List<BillChunk> chunks = new ArrayList<>();
        int pageNum = 1;
        for (String billText : billsText) {
            if (billText.trim().isEmpty()) continue;
            
            Map<String, Object> docMeta = new HashMap<>(singleChunk.getDocumentMetadata());
            Map<String, Object> layMeta = new HashMap<>(singleChunk.getLayoutMetadata());
            layMeta.put("splitType", "fallbackHeaderSplit");
            
            chunks.add(BillChunk.builder()
                    .companyName(singleChunk.getCompanyName())
                    .pageNumber(pageNum++)
                    .extractedText(billText)
                    .extractedTables(singleChunk.getExtractedTables()) // reference original tables
                    .documentMetadata(docMeta)
                    .layoutMetadata(layMeta)
                    .build());
        }
        return chunks;
    }
}
