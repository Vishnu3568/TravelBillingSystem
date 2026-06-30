package com.travels.billing.service;

import com.travels.billing.model.BillChunk;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFRun;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

public class DocumentAnalyzerServiceTest {

    private final DocumentAnalyzerService documentAnalyzerService = new DocumentAnalyzerService();

    @Test
    public void testDocumentSegmentationFallback() throws Exception {
        // Create a mocked docx in memory with recurring markers
        XWPFDocument doc = new XWPFDocument();
        XWPFParagraph p1 = doc.createParagraph();
        XWPFRun r1 = p1.createRun();
        r1.setText("Sri Tulja Bhavani Travels\nBill No: BILL-001\nDuty Slip: DS-100\nAmount: 3000");

        XWPFParagraph p2 = doc.createParagraph();
        XWPFRun r2 = p2.createRun();
        r2.setText("Sri Tulja Bhavani Travels\nBill No: BILL-002\nDuty Slip: DS-101\nAmount: 4000");

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        doc.write(out);
        doc.close();

        ByteArrayInputStream in = new ByteArrayInputStream(out.toByteArray());
        List<BillChunk> chunks = documentAnalyzerService.analyzeAndSplitDocument(in, "test_file.docx");
        
        // Assert that the fallback text segmenter correctly splits by "Bill No" or "Duty Slip"
        assertNotNull(chunks);
        assertTrue(chunks.size() >= 2, "Should split document into at least two bill chunks.");
        assertEquals("Sri Tulja Bhavani Travels", chunks.get(0).getCompanyName());
    }
}
