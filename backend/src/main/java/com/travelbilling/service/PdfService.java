package com.travelbilling.service;

import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.geom.PageSize;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.borders.Border;
import com.itextpdf.layout.borders.DoubleBorder;
import com.itextpdf.layout.borders.SolidBorder;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import com.itextpdf.layout.properties.VerticalAlignment;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelbilling.dto.ChargeDTO;
import com.travelbilling.entity.Bill;
import com.travelbilling.repository.BillRepository;
import com.travelbilling.util.NumberToWordsUtil;
import java.io.ByteArrayOutputStream;
import java.time.format.DateTimeFormatter;
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
            document.setMargins(15, 15, 15, 15);

            // 1. MASTER PAGE BORDER (Double Border)
            Table pageWrapper = new Table(UnitValue.createPercentArray(new float[]{100}))
                    .useAllAvailableWidth()
                    .setMinHeight(PageSize.A4.getHeight() - 30) // Lock to A4 height
                    .setBorder(new DoubleBorder(3));

            Cell innerCell = new Cell()
                    .setBorder(new SolidBorder(0.8f)) // Inner bold border
                    .setPadding(30)
                    .setVerticalAlignment(VerticalAlignment.TOP);

            // 2. HEADER SECTION
            innerCell.add(new Paragraph("SRI TULJA BHAVANI TRAVELS")
                    .setFontSize(26)
                    .setBold()
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(0));
            
            innerCell.add(new Paragraph("RENT-A-CAR")
                    .setFontSize(14)
                    .setBold()
                    .setFontColor(new DeviceRgb(220, 38, 38)) // Professional Red
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(5));
            
            innerCell.add(new Paragraph("1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016")
                    .setFontSize(8)
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(0));
            
            innerCell.add(new Paragraph("srituljabhavanitravels.rentacar@gmail.com")
                    .setFontSize(8)
                    .setUnderline()
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(25));

            // 3. BILL META DATA
            Table metaTable = new Table(UnitValue.createPercentArray(new float[]{60, 40}))
                    .useAllAvailableWidth()
                    .setMarginBottom(15);
            
            metaTable.addCell(new Cell().add(new Paragraph("Bill No. " + bill.getBillNumber())).setBorder(Border.NO_BORDER).setFontSize(10));
            metaTable.addCell(new Cell().add(new Paragraph("Date: " + bill.getBillDate().format(DATE_FORMATTER))).setBorder(Border.NO_BORDER).setTextAlignment(TextAlignment.RIGHT).setFontSize(10));
            
            metaTable.addCell(new Cell().add(new Paragraph("\nTo.")).setBorder(Border.NO_BORDER).setFontSize(10).setPaddingBottom(0));
            metaTable.addCell(new Cell().setBorder(Border.NO_BORDER));
            
            metaTable.addCell(new Cell().add(new Paragraph(bill.getCompanyName().toUpperCase())).setBorder(Border.NO_BORDER).setBold().setFontSize(11));
            metaTable.addCell(new Cell().setBorder(Border.NO_BORDER));
            
            innerCell.add(metaTable);

            // 4. MAIN INVOICE TABLE (9 COLUMNS)
            Table mainTable = new Table(UnitValue.createPercentArray(new float[]{10, 10, 15, 8, 8, 8, 8, 18, 15}))
                    .useAllAvailableWidth();

            // Table Headers with SOLID borders
            String[] headers = {"Duty Slip", "Date", "Vehicle", "Kms", "Hrs", "Extra Kms", "Extra Hrs", "Amt", "Total"};
            for (String h : headers) {
                mainTable.addHeaderCell(new Cell().add(new Paragraph(h).setBold().setFontSize(8)).setTextAlignment(TextAlignment.CENTER).setBorder(new SolidBorder(0.5f)));
            }

            // Calculation Constants
            double kms = bill.getTotalKms() != null ? bill.getTotalKms() : 0;
            double hrs = bill.getTotalHours() != null ? bill.getTotalHours() : 0;
            String vType = (bill.getVehicleType() != null ? bill.getVehicleType() : "SEDAN").toUpperCase();
            boolean isLongTrip = kms > 200;

            // --- BASE ROW ---
            mainTable.addCell(createCell(bill.getDutySlipNo(), TextAlignment.CENTER));
            mainTable.addCell(createCell(bill.getTripDate().format(TRIP_DATE_FORMATTER), TextAlignment.CENTER));
            mainTable.addCell(createCell(bill.getVehicleName(), TextAlignment.LEFT));
            mainTable.addCell(createCell(String.valueOf((int)kms), TextAlignment.RIGHT));
            mainTable.addCell(createCell(String.valueOf((int)hrs), TextAlignment.RIGHT));
            mainTable.addCell(createCell("", TextAlignment.CENTER));
            mainTable.addCell(createCell("", TextAlignment.CENTER));
            
            if (isLongTrip) {
                double rate = vType.contains("CRYSTA") ? 18 : 14;
                mainTable.addCell(createCell(((int)kms) + "x" + ((int)rate), TextAlignment.CENTER));
                mainTable.addCell(createCell(String.format("%.2f", kms * rate), TextAlignment.RIGHT).setBold());
            } else {
                mainTable.addCell(createCell("8/80", TextAlignment.CENTER));
                mainTable.addCell(createCell("2800.00", TextAlignment.RIGHT).setBold());

                // EXTRA KM ROW
                if (kms > 80) {
                    for(int i=0; i<5; i++) mainTable.addCell(createCell("", TextAlignment.CENTER));
                    mainTable.addCell(createCell(((int)kms-80) + "x16", TextAlignment.CENTER));
                    mainTable.addCell(createCell("", TextAlignment.CENTER));
                    mainTable.addCell(createCell("", TextAlignment.CENTER));
                    mainTable.addCell(createCell(String.format("%.2f", (kms-80)*16), TextAlignment.RIGHT).setBold());
                }
                // EXTRA HR ROW
                if (hrs > 8) {
                    for(int i=0; i<6; i++) mainTable.addCell(createCell("", TextAlignment.CENTER));
                    mainTable.addCell(createCell(((int)hrs-8) + "x130", TextAlignment.CENTER));
                    mainTable.addCell(createCell("", TextAlignment.CENTER));
                    mainTable.addCell(createCell(String.format("%.2f", (hrs-8)*130), TextAlignment.RIGHT).setBold());
                }
            }

            // ADDITIONAL CHARGES (Filter 0)
            List<ChargeDTO> charges = deserializeCharges(bill.getDynamicCharges());
            if (charges != null) {
                for (ChargeDTO charge : charges) {
                    String name = charge.getName().toLowerCase();
                    if (name.contains("base amount") || name.contains("extra km") || name.contains("extra hours") || name.contains("distance charge")) continue;
                    if (charge.getAmount() <= 0) continue;

                    for(int i=0; i<7; i++) mainTable.addCell(new Cell().setBorder(new SolidBorder(0.5f))); // Maintain grid
                    mainTable.addCell(createCell(charge.getName(), TextAlignment.CENTER));
                    mainTable.addCell(createCell(String.format("%.2f", charge.getAmount()), TextAlignment.RIGHT).setBold());
                }
            }

            // GRAND TOTAL ROW
            Cell totalLabel = new Cell(1, 8).add(new Paragraph("Grand Total")).setBold().setTextAlignment(TextAlignment.CENTER).setBorder(new SolidBorder(0.5f));
            mainTable.addCell(totalLabel);
            mainTable.addCell(new Cell().add(new Paragraph(String.format("%.2f", bill.getGrandTotal()))).setBold().setTextAlignment(TextAlignment.RIGHT).setBorder(new SolidBorder(0.5f)));

            innerCell.add(mainTable);

            // 5. AMOUNT IN WORDS
            String words = NumberToWordsUtil.convertToRupees(bill.getGrandTotal()).toUpperCase();
            innerCell.add(new Paragraph("\nRupees (in words):  " + words + " ONLY")
                    .setFontSize(10)
                    .setBold()
                    .setMarginTop(15)
                    .setMarginBottom(15));

            // 6. BOTTOM SPACER (To push footer)
            Table spacer = new Table(1).useAllAvailableWidth().setBorder(Border.NO_BORDER);
            spacer.addCell(new Cell().setMinHeight(50).setBorder(Border.NO_BORDER));
            innerCell.add(spacer);

            // 7. SIGNATURE SECTION
            Table footerTable = new Table(UnitValue.createPercentArray(new float[]{50, 50}))
                    .useAllAvailableWidth()
                    .setMarginTop(20);

            Cell customerCell = new Cell().setBorder(Border.NO_BORDER);
            customerCell.add(new Paragraph("For " + bill.getContactPerson()).setUnderline().setFontSize(9));
            customerCell.add(new Paragraph("\nBooked by " + bill.getCompanyName()).setFontSize(9));
            footerTable.addCell(customerCell);

            Cell agencyCell = new Cell().setBorder(Border.NO_BORDER).setTextAlignment(TextAlignment.RIGHT);
            agencyCell.add(new Paragraph("For Sri Tulja Bhavani Travels").setBold().setFontSize(10));
            agencyCell.add(new Paragraph("\n\n\nManager").setFontSize(9));
            footerTable.addCell(agencyCell);

            innerCell.add(footerTable);

            // 8. CONTACT LINE
            innerCell.add(new Paragraph("\nMobile: 9440522814, 9989208711, 9000240410")
                    .setFontSize(8)
                    .setTextAlignment(TextAlignment.RIGHT));

            pageWrapper.addCell(innerCell);
            document.add(pageWrapper);
            document.close();
        } catch (Exception e) {
            throw new RuntimeException("Critical failure in PDF generation", e);
        }

        return out.toByteArray();
    }

    private Cell createCell(String text, TextAlignment align) {
        return new Cell().add(new Paragraph(text != null ? text : "")).setFontSize(8.5f).setTextAlignment(align).setBorder(new SolidBorder(0.5f));
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
