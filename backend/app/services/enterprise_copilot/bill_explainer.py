import json
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models.bill import Bill
from app.models.learning import CorrectionHistory

logger = logging.getLogger("bill_explainer")

class BillExplainer:
    @staticmethod
    def explain_bill(db: Session, bill_id: int) -> Dict[str, Any]:
        """
        Gathers database, coordinate, confidence, and correction history
        associated with a bill to produce a complete explanation.
        """
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            return {"error": f"Bill with ID {bill_id} not found."}

        explanation = {
            "bill_number": bill.bill_number,
            "company_name": bill.company_name,
            "grand_total": bill.grand_total,
            "duty_slip_no": bill.duty_slip_no,
            "fields": {}
        }

        # 1. Parse raw values/original doc if present
        raw_vals = {}
        if bill.raw_values:
            try:
                raw_vals = json.loads(bill.raw_values)
            except Exception:
                pass

        # 2. Query corrections for this bill
        corrections = db.query(CorrectionHistory).filter(
            CorrectionHistory.bill_number == bill.bill_number
        ).all()
        corr_map = {c.field_type: c for c in corrections}

        # 3. Compile explanation for main fields
        fields_to_check = [
            ("companyName", "HEADER_COMPANY", bill.company_name),
            ("billNumber", "HEADER_BILL_NUMBER", bill.bill_number),
            ("dutySlipNo", "HEADER_DUTY_SLIP", bill.duty_slip_no),
            ("totalAmount", "TOTAL_AMOUNT", bill.grand_total),
            ("vehicleNumber", "VEHICLE_NUMBER", bill.vehicle_name)
        ]

        for field_key, label_name, final_val in fields_to_check:
            # Check if there is a correction
            corr = corr_map.get(field_key)
            
            field_expl = {
                "final_value": str(final_val),
                "original_ai_value": corr.original_value if corr else str(final_val),
                "was_corrected": corr is not None,
                "confidence": corr.ai_confidence if corr else 1.0,
                "reviewer": corr.reviewer if corr else "AI",
                "coordinates": {
                    "table": corr.table_number if corr else 1,
                    "row": corr.row_index if corr else 0,
                    "col": corr.column_index if corr else 0
                }
            }
            explanation["fields"][field_key] = field_expl

        return explanation

    @staticmethod
    def get_structured_explanation_text(explanation: Dict[str, Any]) -> str:
        """
        Formats structured explanation data into a clean, markdown explanation block.
        """
        if "error" in explanation:
            return explanation["error"]

        text = [
            f"## Invoice Explanation: Bill #{explanation['bill_number']}",
            f"- **Customer Company**: {explanation['company_name']}",
            f"- **Duty Slip Number**: {explanation['duty_slip_no']}",
            f"- **Grand Total**: ₹{explanation['grand_total']}",
            "\n### AI Extraction & Reviewer Corrections Details:",
        ]

        for field, details in explanation["fields"].items():
            text.append(f"\n#### Field: `{field}`")
            text.append(f"  * **Saved Value**: '{details['final_value']}'")
            if details["was_corrected"]:
                text.append(f"  * **Reviewer Edit**: Yes. Corrected from '{details['original_ai_value']}' by Reviewer '{details['reviewer']}'.")
            else:
                text.append(f"  * **Reviewer Edit**: No. Accepted directly from AI extraction.")
            text.append(f"  * **AI Confidence**: {details['confidence'] * 100:.1f}%")
            coords = details["coordinates"]
            text.append(f"  * **Document Location**: Table {coords['table']}, Row {coords['row']}, Col {coords['col']}")

        return "\n".join(text)
