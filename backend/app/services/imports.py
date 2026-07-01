import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.company import Company
from app.models.bill import Bill
from app.services.docx_segmenter import DocxSegmenterService
from app.services.ai_extraction import AiExtractionService
from app.services.validation_service import ValidationService
from app.services.bills import BillService
from app.services.audit_log import AuditLogService
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
                chunks = DocxSegmenterService.segment_docx(file_bytes, file_name)
                
                # Extract companies page by page to avoid mixing up data
                for chunk in chunks:
                    company_data = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name)
                    name = company_data.get("company")
                    if not name or not name.strip() or name.strip().lower() == "null":
                        continue
                    
                    name_trimmed = name.strip()
                    existing = db.query(Company).filter(Company.name == name_trimmed).first()
                    
                    if existing:
                        address = company_data.get("address") or company_data.get("pickup") or company_data.get("drop")
                        if address and address.strip():
                            existing.address = address.strip()
                        # If a GST number was found
                        gst = company_data.get("gstNumber")
                        if gst and gst.strip() and gst.strip().lower() != "null":
                            existing.gst_number = gst.strip()
                    else:
                        address = company_data.get("address") or company_data.get("pickup") or company_data.get("drop")
                        gst = company_data.get("gstNumber")
                        new_comp = Company(
                            name=name_trimmed,
                            address=address,
                            gst_number=gst if (gst and gst.strip().lower() != "null") else None
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
        """
        Segment, extract, validate, and save bills page-by-page.
        Ensures failed pages are recorded separately without interrupting successful saves.
        """
        success_count = 0
        duplicate_count = 0
        failure_count = 0
        errors = []

        for f in files:
            file_name = f.get("filename", "unknown")
            file_bytes = f.get("content", b"")
            if not file_bytes:
                continue

            try:
                logger.info(f"Starting rebuilt page-segmented bill import for file: {file_name}")
                chunks = DocxSegmenterService.segment_docx(file_bytes, file_name)
                
                # Parse and save page-by-page
                for chunk in chunks:
                    try:
                        logger.info(f"Parsing page {chunk.page_number}/{len(chunks)} of {file_name}")
                        extracted_dict = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name)
                        bill_res = AiExtractionService.map_to_bill_response(extracted_dict)
                        
                        # Validate the bill
                        warnings = ValidationService.validate_bill(db, bill_res)
                        
                        # Check critical validation issues (no slip number or no company name)
                        has_critical_error = any("Missing mandatory field" in w or "missing or zero" in w for w in warnings)
                        is_duplicate = any("Duplicate bill warning" in w for w in warnings)
                        
                        if has_critical_error:
                            failure_count += 1
                            err_msg = f"Page {chunk.page_number}: Validation failed - {', '.join(warnings)}"
                            errors.append(err_msg)
                            logger.warning(err_msg)
                            
                            # Record failed page in system audit logs
                            AuditLogService.log_action(
                                db=db,
                                action="BILL_IMPORT_FAILED",
                                module="IMPORT",
                                description=f"File: {file_name} (Page {chunk.page_number}) - {err_msg}",
                                username=created_by,
                                role="OWNER",
                                ip_address=ip
                            )
                            continue
                            
                        if is_duplicate:
                            duplicate_count += 1
                            logger.info(f"Page {chunk.page_number}: Duplicate detected. Skipped saving.")
                            continue

                        # Save this single bill independently
                        saved = BillService.save_ai_parsed_bills(db, [bill_res], created_by, ip)
                        if saved:
                            success_count += 1
                        else:
                            failure_count += 1
                            err_msg = f"Page {chunk.page_number}: Database save failed."
                            errors.append(err_msg)
                            
                            AuditLogService.log_action(
                                db=db,
                                action="BILL_IMPORT_FAILED",
                                module="IMPORT",
                                description=f"File: {file_name} (Page {chunk.page_number}) - {err_msg}",
                                username=created_by,
                                role="OWNER",
                                ip_address=ip
                            )
                    except Exception as page_ex:
                        failure_count += 1
                        err_msg = f"Page {chunk.page_number}: Processing exception - {str(page_ex)}"
                        errors.append(err_msg)
                        logger.error(err_msg)
                        
                        AuditLogService.log_action(
                            db=db,
                            action="BILL_IMPORT_FAILED",
                            module="IMPORT",
                            description=f"File: {file_name} (Page {chunk.page_number}) - {err_msg}",
                            username=created_by,
                            role="OWNER",
                            ip_address=ip
                        )
            except Exception as doc_ex:
                logger.error(f"Failed to process document {file_name}: {doc_ex}")
                errors.append(f"File {file_name}: {str(doc_ex)}")
                failure_count += 1

        return {
            "successCount": success_count,
            "duplicateCount": duplicate_count,
            "failureCount": failure_count,
            "errors": errors
        }

    @staticmethod
    def parse_bills_only(db: Session, files: List[Dict[str, Any]]) -> List[AiBillResponse]:
        """
        Parses all pages in the uploaded docx files, validates each, and attaches warnings.
        Does not write to the database. Used for previewing before final save.
        """
        all_parsed = []
        for f in files:
            file_name = f.get("filename", "unknown")
            file_bytes = f.get("content", b"")
            if not file_bytes:
                continue

            try:
                logger.info(f"AI parsing file for preview: {file_name}")
                chunks = DocxSegmenterService.segment_docx(file_bytes, file_name)

                for chunk in chunks:
                    try:
                        logger.info(f"Parsing preview for page {chunk.page_number}/{len(chunks)}")
                        extracted_dict = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name)
                        bill_res = AiExtractionService.map_to_bill_response(extracted_dict)
                        
                        # Validate and attach warnings
                        warnings = ValidationService.validate_bill(db, bill_res)
                        bill_res.warnings = warnings
                        
                        all_parsed.append(bill_res)
                    except Exception as page_ex:
                        logger.error(f"Preview parsing failed for page {chunk.page_number} in {file_name}: {page_ex}")
            except Exception as e:
                logger.error(f"Failed to segment preview document {file_name}: {e}")
        return all_parsed
