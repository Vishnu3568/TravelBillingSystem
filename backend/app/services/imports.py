import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.company import Company
from app.models.bill import Bill
from app.services.docx_extractor import DocxExtractionService
from app.services.gemini import gemini_service
from app.services.bills import BillService
from app.schemas.ai import AiBillResponse


logger = logging.getLogger("bulk_import_service")

class BulkImportService:
    @staticmethod
    def import_companies(db: Session, files: List[Dict[str, Any]], current_user: str, current_role: str, ip: str) -> Dict[str, Any]:
        success_count = 0
        failure_count = 0
        errors = []

        for f in files:
            file_name = f.get("filename", "unknown")
            file_bytes = f.get("content", b"")
            try:
                if not file_bytes:
                    continue
                
                logger.info(f"Starting AI-assisted company import for file: {file_name}")
                raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
                company_data = gemini_service.extract_companies(raw_text)

                for data in company_data:
                    name = data.get("name")
                    if not name or not name.strip():
                        continue
                    
                    name_trimmed = name.strip()
                    existing = db.query(Company).filter(Company.name == name_trimmed).first()
                    
                    if existing:
                        if data.get("address") and data.get("address").strip():
                            existing.address = data.get("address").strip()
                        if data.get("gstNumber") and data.get("gstNumber").strip():
                            existing.gst_number = data.get("gstNumber").strip()
                    else:
                        new_comp = Company(
                            name=name_trimmed,
                            address=data.get("address"),
                            gst_number=data.get("gstNumber")
                        )
                        db.add(new_comp)
                    
                    db.commit()
                    success_count += 1
            except Exception as e:
                logger.error(f"Company import failed for file {file_name}: {e}")
                failure_count += 1
                errors.append(f"{file_name}: {str(e)}")

        return {
            "successCount": success_count,
            "failureCount": failure_count,
            "errors": errors
        }

    @staticmethod
    def import_bills(db: Session, files: List[Dict[str, Any]], created_by: str, ip: str) -> Dict[str, Any]:
        success_count = 0
        duplicate_count = 0
        failure_count = 0
        errors = []

        for f in files:
            file_name = f.get("filename", "unknown")
            file_bytes = f.get("content", b"")
            try:
                if not file_bytes:
                    continue
                
                logger.info(f"Starting AI-assisted bulk bill import for file: {file_name}")
                raw_text = DocxExtractionService.extract_raw_text(file_bytes, file_name)
                ai_responses_dicts = gemini_service.parse_bill_text(raw_text)

                if not ai_responses_dicts:
                    failure_count += 1
                    errors.append(f"{file_name}: AI failed to extract any bills.")
                    continue

                # Convert response dictionaries to schemas
                ai_responses = []
                for res_dict in ai_responses_dicts:
                    # Clean/rename mapping if necessary, or pass straight to model
                    # Convert dynamic charges to schemas
                    chgs = []
                    if "dynamicCharges" in res_dict and res_dict["dynamicCharges"]:
                        for c in res_dict["dynamicCharges"]:
                            chgs.append(c)
                    elif "charges" in res_dict and res_dict["charges"]:
                        # Fallback for old schema name
                        for c in res_dict["charges"]:
                            chgs.append(c)
                    
                    ai_responses.append(AiBillResponse(
                        dutySlipNo=res_dict.get("dutySlipNo") or res_dict.get("billNumber"),
                        billDate=res_dict.get("billDate") or res_dict.get("date"),
                        companyName=res_dict.get("companyName"),
                        vehicleNumber=res_dict.get("vehicleNumber"),
                        vehicleType=res_dict.get("vehicleType"),
                        totalKms=res_dict.get("totalKms") or res_dict.get("totalKm"),
                        totalHours=res_dict.get("totalHours"),
                        dynamicCharges=chgs,
                        totalAmount=res_dict.get("totalAmount"),
                        warnings=res_dict.get("warnings")
                    ))
                
                saved_list = BillService.save_ai_parsed_bills(db, ai_responses, created_by, ip)

                if not saved_list:
                    # Check if all parsed bills were duplicates
                    all_duplicates = True
                    for ai in ai_responses:
                        ds_no = ai.dutySlipNo
                        if not ds_no or not ds_no.strip() or ds_no == "---":
                            all_duplicates = False
                            break
                        # Check existence
                        exists = db.query(Bill).filter(
                            Bill.duty_slip_no == ds_no.strip(),
                            Bill.company_name == ai.companyName
                        ).first()
                        if not exists:
                            all_duplicates = False
                            break
                    
                    if all_duplicates:
                        duplicate_count += len(ai_responses)
                    else:
                        failure_count += 1
                        errors.append(f"{file_name}: Failed to save AI parsed bills.")
                else:
                    success_count += len(saved_list)
                    if len(saved_list) < len(ai_responses):
                        duplicate_count += (len(ai_responses) - len(saved_list))

            except Exception as e:
                logger.error(f"Import failed for file {file_name}: {e}")
                failure_count += 1
                errors.append(f"{file_name}: {str(e)}")

        return {
            "successCount": success_count,
            "duplicateCount": duplicate_count,
            "failureCount": failure_count,
            "errors": errors
        }
