package com.travelbilling.service;

import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.geom.PageSize;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.borders.Border;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.dto.ChargeDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.util.NumberToWordsUtil;
import java.io.ByteArrayOutputStream;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class PdfService {
    private final BillRepository billRepository;
    private final ObjectMapper objectMapper;
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("dd-MM-yyyy");
    private static final DateTimeFormatter TRIP_DATE_FORMATTER = DateTimeFormatter.ofPattern("dd-MM-yy");

    public byte[] generateInvoicePdf(Long billId) {
        Bill bill = billRepository.findById(billId)
                .orElseThrow(() -> new IllegalArgumentException("Bill not found"));

        ByteArrayOutputStream out = new ByteArrayOutputStream();

        try {
            PdfWriter writer = new PdfWriter(out);
            PdfDocument pdf = new PdfDocument(writer);
            Document document = new Document(pdf, PageSize.A4);
            document.setMargins(40, 40, 40, 40);

            // 1. Header (Centered)
            document.add(new Paragraph("SRI TULJA BHAVANI TRAVELS")
                    .setFontSize(24)
                    .setBold()
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(0));
            
            document.add(new Paragraph("RENT-A-CAR")
                    .setFontSize(14)
                    .setBold()
                    .setFontColor(new DeviceRgb(255, 0, 0))
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(2));
            
            document.add(new Paragraph("1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016")
                    .setFontSize(8)
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(0));
            
            document.add(new Paragraph("srituljabhavanitravels.rentacar@gmail.com")
                    .setFontSize(8)
                    .setUnderline()
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(20));

            // 2. Bill Meta Row (Bill No & Date)
            Table metaTable = new Table(UnitValue.createPercentArray(new float[]{70, 30}))
                    .useAllAvailableWidth()
                    .setMarginBottom(10);
            
            metaTable.addCell(new Cell().add(new Paragraph("Bill No. " + bill.getBillNumber())).setBorder(Border.NO_BORDER).setFontSize(10));
            metaTable.addCell(new Cell().add(new Paragraph("Date: " + bill.getBillDate().format(DATE_FORMATTER))).setBorder(Border.NO_BORDER).setTextAlignment(TextAlignment.RIGHT).setFontSize(10));
            
            metaTable.addCell(new Cell().add(new Paragraph("\nTo.")).setBorder(Border.NO_BORDER).setFontSize(10));
            metaTable.addCell(new Cell().setBorder(Border.NO_BORDER));
            
            metaTable.addCell(new Cell().add(new Paragraph(bill.getCompanyName())).setBorder(Border.NO_BORDER).setBold().setFontSize(11));
            metaTable.addCell(new Cell().setBorder(Border.NO_BORDER));
            
            document.add(metaTable);

            // 3. Main Table (9 Columns)
            Table mainTable = new Table(UnitValue.createPercentArray(new float[]{10, 10, 15, 8, 8, 8, 8, 18, 15}))
                    .useAllAvailableWidth()
                    .setMarginBottom(10);

            // Header Cells
            String[] headers = {"Duty Slip No", "Date", "Vehicle No", "Total Kms", "Total Hrs", "Extra Kms", "Extra Hrs", "Amt", "Total Amount"};
            for (String header : headers) {
                mainTable.addHeaderCell(new Cell().add(new Paragraph(header).setBold().setFontSize(8.5f)).setTextAlignment(TextAlignment.CENTER));
            }

            // CALCULATION LOGIC
            double kms = bill.getTotalKms() != null ? bill.getTotalKms() : 0;
            double hrs = bill.getTotalHours() != null ? bill.getTotalHours() : 0;
            String vType = bill.getVehicleType() != null ? bill.getVehicleType().toUpperCase() : "SEDAN";
            boolean isLongTrip = kms > 200;

            String extraKmText = "";
            String extraHrText = "";
            String amtText = "";
            double rowTotal = 0;

            if (isLongTrip) {
                double rate = vType.contains("CRYSTA") ? 18 : 14;
                amtText = ((int)kms) + "x" + ((int)rate);
                rowTotal = kms * rate;
            } else {
                amtText = "8/80";
                rowTotal = 2800;

                if (kms > 80) {
                    int extraKm = (int)kms - 80;
                    extraKmText = extraKm + "x16";
                    rowTotal += extraKm * 16;
                }

                if (hrs > 8) {
                    int extraHr = (int)hrs - 8;
                    extraHrText = extraHr + "x130";
                    rowTotal += extraHr * 130;
                }
            }

            // Trip Row
            mainTable.addCell(new Cell().add(new Paragraph(bill.getDutySlipNo() != null ? bill.getDutySlipNo() : "")).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(bill.getTripDate() != null ? bill.getTripDate().format(TRIP_DATE_FORMATTER) : "")).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(bill.getVehicleName() != null ? bill.getVehicleName() : "")).setFontSize(8.5f).setTextAlignment(TextAlignment.LEFT));
            mainTable.addCell(new Cell().add(new Paragraph(String.valueOf((int)kms))).setFontSize(8.5f).setTextAlignment(TextAlignment.RIGHT));
            mainTable.addCell(new Cell().add(new Paragraph(String.valueOf((int)hrs))).setFontSize(8.5f).setTextAlignment(TextAlignment.RIGHT));
            mainTable.addCell(new Cell().add(new Paragraph(extraKmText)).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(extraHrText)).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(amtText)).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(String.format("%.2f", rowTotal))).setFontSize(9).setBold().setTextAlignment(TextAlignment.RIGHT));

            // Additional Charges
            List<ChargeDTO> charges = deserializeCharges(bill.getDynamicCharges());
            if (charges != null) {
                for (ChargeDTO charge : charges) {
                    String name = charge.getName().toLowerCase();
                    // Skip system charges already handled in trip row
                    if (name.contains("base amount") || name.contains("extra km") || 
                        name.contains("extra hours") || name.contains("distance charge")) continue;

                    for (int j = 0; j < 7; j++) mainTable.addCell(new Cell().add(new Paragraph("")).setBorder(Border.NO_BORDER));
                    mainTable.addCell(new Cell().add(new Paragraph(charge.getName())).setFontSize(8.5f).setTextAlignment(TextAlignment.CENTER));
                    mainTable.addCell(new Cell().add(new Paragraph(String.format("%.2f", charge.getAmount()))).setFontSize(9).setBold().setTextAlignment(TextAlignment.RIGHT));
                }
            }

            // Grand Total Row
            for (int i = 0; i < 7; i++) mainTable.addCell(new Cell().setBorder(Border.NO_BORDER));
            mainTable.addCell(new Cell().add(new Paragraph("Grand Total").setBold().setFontSize(9)).setTextAlignment(TextAlignment.CENTER));
            mainTable.addCell(new Cell().add(new Paragraph(String.format("%.2f", bill.getGrandTotal())).setBold().setFontSize(10)).setTextAlignment(TextAlignment.RIGHT));

            document.add(mainTable);

            // 4. Amount in Words
            String words = NumberToWordsUtil.convertToRupees(bill.getGrandTotal()).toUpperCase();
            document.add(new Paragraph("Rupees (in words):  " + words + " ONLY")
                    .setFontSize(10)
                    .setBold()
                    .setMarginBottom(30));

            // 5. Footer Section
            Table footerTable = new Table(UnitValue.createPercentArray(new float[]{50, 50}))
                    .useAllAvailableWidth();

            // Left Footer
            Cell leftFooter = new Cell().setBorder(Border.NO_BORDER);
            leftFooter.add(new Paragraph("For " + (bill.getContactPerson() != null ? bill.getContactPerson() : "")).setUnderline().setFontSize(9));
            leftFooter.add(new Paragraph("\nBooked by " + (bill.getCompanyName())).setFontSize(9));
            footerTable.addCell(leftFooter);

            // Right Footer
            Cell rightFooter = new Cell().setBorder(Border.NO_BORDER).setTextAlignment(TextAlignment.RIGHT);
            rightFooter.add(new Paragraph("For Sri Tulja Bhavani Travels").setBold().setFontSize(10));
            rightFooter.add(new Paragraph("\n\n\nManager").setFontSize(9));
            footerTable.addCell(rightFooter);

            document.add(footerTable);

            // Mobile Numbers
            document.add(new Paragraph("\nMobile: 98480 12345, 98480 67890")
                    .setFontSize(8)
                    .setTextAlignment(TextAlignment.RIGHT));

            document.close();
        } catch (Exception e) {
            throw new RuntimeException("Error generating PDF", e);
        }

        return out.toByteArray();
    }

    private List<ChargeDTO> deserializeCharges(String chargesJson) {
        if (chargesJson == null || chargesJson.isBlank()) return java.util.Collections.emptyList();
        try {
            return objectMapper.readValue(chargesJson, new TypeReference<List<ChargeDTO>>() {});
        } catch (Exception e) {
            return java.util.Collections.emptyList();
        }
    }
}
