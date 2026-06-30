import re
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.bill import Bill
from app.schemas.ai import AiBillResponse


logger = logging.getLogger("validation_service")

# Regex to check standard Indian vehicle plate numbers
# E.g. AP-09-TV-1234, TS08EL1234, DL-1C-AA-1111, etc.
VEHICLE_PLATE_REGEX = r'^[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}$'

class ValidationService:
    @staticmethod
    def validate_bill(db: Session, bill: AiBillResponse) -> List[str]:
        """
        Validates the extracted AiBillResponse object.
        Returns a list of warnings/errors. If list is empty, validation passed.
        """
        warnings = []
        
        # 1. Missing Fields Check
        if not bill.dutySlipNo or bill.dutySlipNo.strip() in ["", "---", "null"]:
            warnings.append("Missing mandatory field: Duty Slip Number")
            
        if not bill.companyName or bill.companyName.strip() in ["", "---", "null"]:
            warnings.append("Missing mandatory field: Company Name")
            
        if not bill.vehicleNumber or bill.vehicleNumber.strip() in ["", "---", "null"]:
            warnings.append("Missing mandatory field: Vehicle Number")
            
        if not bill.totalAmount or bill.totalAmount <= 0.0:
            warnings.append("Total Amount is missing or zero/negative")

        # 2. Date Verification
        if bill.billDate:
            try:
                # Expecting YYYY-MM-DD
                datetime.strptime(bill.billDate.strip(), "%Y-%m-%d")
            except ValueError:
                warnings.append(f"Invalid date format: '{bill.billDate}'. Expected YYYY-MM-DD.")
        else:
            warnings.append("Missing Bill Date")

        # 3. Duplicate Bill Check
        if bill.dutySlipNo and bill.companyName:
            ds_clean = bill.dutySlipNo.strip()
            comp_clean = bill.companyName.strip()
            if ds_clean and comp_clean:
                # Query DB to check if this duty slip and company combo already exists
                existing = db.query(Bill).filter(
                    Bill.duty_slip_no == ds_clean,
                    Bill.company_name == comp_clean
                ).first()
                if existing:
                    warnings.append(f"Duplicate bill warning: Duty Slip {ds_clean} already exists in the database for {comp_clean}.")

        # 4. Vehicle Registration Format Verification
        if bill.vehicleNumber:
            v_num = bill.vehicleNumber.strip().upper()
            # Remove spaces and hyphens for a standard comparison, or check regex directly
            cleaned_v_num = re.sub(r'[-\s]', '', v_num)
            # Try matching original and cleaned
            match1 = re.match(VEHICLE_PLATE_REGEX, v_num)
            match2 = re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$', cleaned_v_num)
            if not (match1 or match2):
                warnings.append(f"Malformed vehicle registration plate number format: '{bill.vehicleNumber}'")

        # 5. Arithmetic / Calculations Check
        # grandTotal = baseAmount + bata + toll + parking + night + other
        # For parsed bills preview, baseAmount might not be directly filled or is equal to totalAmount minus other charges.
        # Let's calculate sum of charges:
        charges_sum = 0.0
        if bill.dynamicCharges:
            for charge in bill.dynamicCharges:
                charges_sum += charge.amount
        
        # If totalAmount is provided, and we have dynamic charges but no baseAmount explicitly separated, 
        # let's make sure the sum of dynamic charges does not exceed the totalAmount.
        if bill.totalAmount and charges_sum > bill.totalAmount:
            warnings.append(f"Arithmetic warning: Sum of line-item charges (₹{charges_sum}) exceeds the Total Amount (₹{bill.totalAmount})")
            
        return warnings
