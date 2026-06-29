import io
import json
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.bill import Bill
from app.utils.number_to_words import NumberToWordsUtil

logger = logging.getLogger("pdf_service")

class PdfService:
    @staticmethod
    def generate_invoice_pdf(db, bill_id: int) -> bytes:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise ValueError("Bill not found")

        buffer = io.BytesIO()
        
        # Margin is 15 points (A4 size is 595.27 x 841.89 points)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15,
            rightMargin=15,
            topMargin=15,
            bottomMargin=15
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            alignment=1, # Center
            spaceAfter=2
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            textColor=colors.HexColor('#DC2626'), # Sri Tulja Bhavani Red
            alignment=1,
            spaceAfter=4
        )
        
        center_small = ParagraphStyle(
            'CenterSmall',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=1
        )
        
        center_small_link = ParagraphStyle(
            'CenterSmallLink',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=1,
            spaceAfter=15
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=12
        )
        
        bold_style = ParagraphStyle(
            'BoldStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12
        )
        
        right_style = ParagraphStyle(
            'RightStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=10,
            alignment=2 # Right
        )
        
        right_bold_style = ParagraphStyle(
            'RightBoldStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            alignment=2
        )
        
        story = []
        
        # Double border drawing callback
        def draw_page_border(canvas, doc_obj):
            width, height = doc_obj.pagesize
            canvas.saveState()
            
            # Outer double border (DoubleBorder(3) in Java iText)
            canvas.setLineWidth(2)
            canvas.setStrokeColor(colors.black)
            canvas.rect(10, 10, width - 20, height - 20)
            
            # Inner border
            canvas.setLineWidth(0.8)
            canvas.rect(13, 13, width - 26, height - 26)
            
            canvas.restoreState()

        story.append(Spacer(1, 15))
        
        # Header text
        story.append(Paragraph("SRI TULJA BHAVANI TRAVELS", title_style))
        story.append(Paragraph("RENT-A-CAR", subtitle_style))
        story.append(Paragraph("1-11-113/3, P2 Sai Shikara Apartments, Shyamlal Building Begumpet, Hyderabad - 500016", center_small))
        story.append(Paragraph("srituljabhavanitravels.rentacar@gmail.com", center_small_link))
        
        # Metadata information
        bill_date_str = bill.bill_date.strftime("%d-%m-%Y") if bill.bill_date else "N/A"
        meta_data = [
            [
                Paragraph(f"Bill No. {bill.bill_number}", normal_style),
                Paragraph(f"Date: {bill_date_str}", right_style)
            ],
            [
                Paragraph("<br/>To.", normal_style),
                ""
            ],
            [
                Paragraph(bill.company_name.upper() if bill.company_name else "", bold_style),
                ""
            ]
        ]
        meta_table = Table(meta_data, colWidths=[339, 226])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))
        
        # 6-Column Main Table
        # Column widths totaling 565 (A4 width 595 - margins 30)
        col_widths = [85, 85, 140, 85, 85, 90]
        trip_date_str = bill.trip_date.strftime("%d-%m-%y") if bill.trip_date else ""
        main_data = [
            [
                Paragraph("<b>Duty Slip</b>", center_small),
                Paragraph("<b>Date</b>", center_small),
                Paragraph("<b>Vehicle Reg</b>", center_small),
                Paragraph("<b>Kms</b>", center_small),
                Paragraph("<b>Hours</b>", center_small),
                Paragraph("<b>Total</b>", center_small)
            ],
            [
                Paragraph(bill.duty_slip_no or "", center_small),
                Paragraph(trip_date_str, center_small),
                Paragraph(bill.vehicle_name or "", center_small),
                Paragraph(str(int(bill.total_kms)) if bill.total_kms is not None else "0", right_style),
                Paragraph(str(int(bill.total_hours)) if bill.total_hours is not None else "0", right_style),
                Paragraph(f"{bill.grand_total:.2f}" if bill.grand_total is not None else "0.00", right_bold_style)
            ]
        ]
        main_table = Table(main_data, colWidths=col_widths)
        main_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(main_table)
        story.append(Spacer(1, 15))
        
        # Charges Table
        charges_data = [
            [
                Paragraph("<b>DESCRIPTION</b>", bold_style),
                Paragraph("<b>AMOUNT</b>", right_bold_style)
            ],
            [
                Paragraph("Base Trip Amount", normal_style),
                Paragraph(f"{bill.base_amount:.2f}" if bill.base_amount is not None else "0.00", right_style)
            ]
        ]
        
        dynamic_charges = []
        if bill.dynamic_charges:
            try:
                dynamic_charges = json.loads(bill.dynamic_charges)
            except Exception as e:
                logger.error(f"Error decoding dynamic charges: {e}")
                
        for chg in dynamic_charges:
            name = chg.get("name", "")
            if "base" in name.lower():
                continue
            amt = float(chg.get("amount", 0.0))
            charges_data.append([
                Paragraph(name, normal_style),
                Paragraph(f"{amt:.2f}", right_style)
            ])
            
        charges_data.append([
            Paragraph("<b>GRAND TOTAL</b>", bold_style),
            Paragraph(f"<b>Rs. {bill.grand_total:.2f}</b>", right_bold_style)
        ])
        
        charges_table = Table(charges_data, colWidths=[395, 170])
        charges_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
        ]))
        story.append(charges_table)
        story.append(Spacer(1, 15))
        
        # Words conversion
        words = NumberToWordsUtil.convert_to_rupees(bill.grand_total or 0.0).upper()
        story.append(Paragraph(f"Rupees (in words):  <b>{words}</b>", bold_style))
        story.append(Spacer(1, 30))
        
        # Signatures
        contact_person = bill.contact_person or ""
        sig_data = [
            [
                Paragraph(f"<u>For {contact_person}</u><br/><br/>Booked by {bill.company_name}", normal_style),
                Paragraph("<b>For Sri Tulja Bhavani Travels</b><br/><br/><br/>Manager", right_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[282, 283])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(sig_table)
        
        story.append(Spacer(1, 15))
        story.append(Paragraph("Mobile: 9440522814, 9989208711, 9000240410", right_style))
        
        doc.build(story, onFirstPage=draw_page_border)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
