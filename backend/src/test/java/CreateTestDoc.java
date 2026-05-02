import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFRun;
import java.io.FileOutputStream;
import java.io.File;

public class CreateTestDoc {
    public static void main(String[] args) throws Exception {
        XWPFDocument document = new XWPFDocument();
        
        // Header (The one AI should ignore)
        XWPFParagraph header = document.createParagraph();
        XWPFRun headerRun = header.createRun();
        headerRun.setText("SRI TULJA BHAVANI TRAVELS & LOGISTICS");
        headerRun.setBold(true);
        
        document.createParagraph().createRun().setText("Travel Agency Service Provider");
        
        // Target (The one AI should find)
        XWPFParagraph to = document.createParagraph();
        to.createRun().setText("To,");
        
        XWPFParagraph client = document.createParagraph();
        client.createRun().setText("C.V. Narsima Murthy");
        
        document.createParagraph().createRun().setText("Subject: Bill for Travel Services");
        
        // Bill Details
        document.createParagraph().createRun().setText("Date: 15-01-2022");
        document.createParagraph().createRun().setText("Duty Slip No: 12345");
        document.createParagraph().createRun().setText("Vehicle: Innova Crysta KA-01-MH-6673");
        document.createParagraph().createRun().setText("Total Kms: 350");
        document.createParagraph().createRun().setText("Total Hours: 12");
        
        // Charges
        document.createParagraph().createRun().setText("Hire Charges: 64500");
        document.createParagraph().createRun().setText("Driver Bata: 500");
        document.createParagraph().createRun().setText("Toll Charges: 150");
        document.createParagraph().createRun().setText("Total Amount: 65150");
        
        try (FileOutputStream out = new FileOutputStream(new File("test-bill.docx"))) {
            document.write(out);
        }
        System.out.println("Test document created: test-bill.docx");
        document.close();
    }
}
