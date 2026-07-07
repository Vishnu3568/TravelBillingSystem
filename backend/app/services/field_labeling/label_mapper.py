from __future__ import annotations

from typing import Dict, Any
from app.services.field_labeling.field_constants import FieldLabel
from app.services.field_labeling.field_models import LabeledDocument

class LabelMapper:
    @staticmethod
    def to_extraction_dict(labeled_doc: LabeledDocument) -> Dict[str, Any]:
        """
        Maps a LabeledDocument's classified elements back to the 26 target billing
        fields schema expected by the validation and save layers.
        """
        extracted = {
            "company": "UNKNOWN",
            "billNumber": "UNKNOWN",
            "invoiceNumber": "UNKNOWN",
            "dutySlip": "UNKNOWN",
            "vehicleNumber": "UNKNOWN",
            "vehicleType": "UNKNOWN",
            "driver": "UNKNOWN",
            "billDate": "UNKNOWN",
            "tripDate": "UNKNOWN",
            "contactPerson": "UNKNOWN",
            "bookedBy": "UNKNOWN",
            "reportingDate": "UNKNOWN",
            "reportingTime": "UNKNOWN",
            "releaseDate": "UNKNOWN",
            "releaseTime": "UNKNOWN",
            "pickup": "UNKNOWN",
            "drop": "UNKNOWN",
            "totalHours": "UNKNOWN",
            "totalKilometers": "UNKNOWN",
            "minimumHours": "UNKNOWN",
            "minimumKilometers": "UNKNOWN",
            "extraHours": "",
            "extraKilometers": "",
            "baseAmount": "0.0",
            "toll": "",
            "parking": "",
            "permit": "",
            "driverBata": "",
            "nightCharges": "",
            "totalAmount": "0.0",
            "remarks": ""
        }

        # Index elements by label
        by_label = {}
        for el in labeled_doc.elements:
            by_label.setdefault(el.label, []).append(el)

        def get_text(label: str, default: str = "UNKNOWN") -> str:
            items = by_label.get(label, [])
            if not items:
                return default
            texts = [i.text for i in items if i.text.strip()]
            return texts[0] if texts else default

        extracted["company"] = get_text(FieldLabel.HEADER_COMPANY.value)
        extracted["billNumber"] = get_text(FieldLabel.HEADER_BILL_NUMBER.value)
        extracted["invoiceNumber"] = get_text(FieldLabel.HEADER_BILL_NUMBER.value)
        extracted["dutySlip"] = get_text(FieldLabel.HEADER_DUTY_SLIP.value)
        extracted["vehicleNumber"] = get_text(FieldLabel.VEHICLE_NUMBER.value)
        extracted["vehicleType"] = get_text(FieldLabel.VEHICLE_TYPE.value)
        extracted["billDate"] = get_text(FieldLabel.HEADER_DATE.value)
        extracted["tripDate"] = get_text(FieldLabel.HEADER_DATE.value)
        extracted["contactPerson"] = get_text(FieldLabel.GUEST_NAME.value)
        extracted["bookedBy"] = get_text(FieldLabel.BOOKED_BY.value)

        extracted["totalHours"] = get_text(FieldLabel.TOTAL_HOURS.value)
        extracted["totalKilometers"] = get_text(FieldLabel.TOTAL_KM.value)

        # Base rental details
        extracted["baseAmount"] = get_text(FieldLabel.BASE_PACKAGE.value, "0.0")

        # Extra charges formulae
        extracted["extraKilometers"] = get_text(FieldLabel.EXTRA_KM_FORMULA.value, "")
        extracted["extraHours"] = get_text(FieldLabel.EXTRA_HOUR_FORMULA.value, "")

        # Individual charge amounts
        extracted["driverBata"] = get_text(FieldLabel.DRIVER_BATA.value, "")
        extracted["toll"] = get_text(FieldLabel.TOLL.value, "")
        extracted["parking"] = get_text(FieldLabel.PARKING.value, "")
        extracted["permit"] = get_text(FieldLabel.PERMIT.value, "")
        extracted["otherCharges"] = get_text(FieldLabel.OTHER_CHARGE.value, "")
        extracted["totalAmount"] = get_text(FieldLabel.TOTAL_AMOUNT.value, "0.0")

        return extracted
