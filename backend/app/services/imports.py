import logging
import requests
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.company import Company
from app.models.bill import Bill
from app.services.docx_segmenter import DocxSegmenterService
from app.services.ai_extraction import AiExtractionService
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.business_validation_service import ValidationService
from app.services.bills import BillService
from app.services.audit_log import AuditLogService
from app.schemas.ai import AiBillResponse

logger = logging.getLogger("bulk_import_service")

class BulkImportService:
    @staticmethod
    def _build_document_intelligence(file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        document_model = DocumentIntelligenceService.extract_document(file_bytes, file_name)
        return document_model.to_json()

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
                _ = BulkImportService._build_document_intelligence(file_bytes, file_name)
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
    def _index_and_retrieve_rag_context(chunk_text: str, filename: str, page_number: int) -> str:
        # 1. Index in RAG by uploading virtual text file
        try:
            files = {
                "file": (f"{filename}_page_{page_number}.txt", chunk_text.encode("utf-8"), "text/plain")
            }
            upload_res = requests.post("http://localhost:9002/upload", files=files, timeout=10)
            if upload_res.status_code != 200:
                logger.warning(f"RAG upload failed: {upload_res.text}")
        except Exception as e:
            logger.warning(f"RAG upload exception: {e}")

        # 2. Query RAG for contextual matching
        try:
            query_payload = {
                "query": f"Find company details, invoice numbers, or duty slip patterns for {filename} page {page_number}",
                "top_k": 3,
                "use_reranker": True
            }
            query_res = requests.post("http://localhost:9002/query", json=query_payload, timeout=10)
            if query_res.status_code == 200:
                ans_data = query_res.json()
                return ans_data.get("answer", "")
        except Exception as e:
            logger.warning(f"RAG query exception: {e}")
        return ""

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
                doc_model = DocumentIntelligenceService.extract_document(file_bytes, file_name)
                document_intelligence = doc_model.to_json()

                labeled_doc = None
                from app.config import settings
                if settings.USE_ENTERPRISE_LABELER:
                    from app.services.field_labeling import FieldLabelingService
                    
                    # Heuristic to detect company name from first page paragraphs or filename
                    company_name = None
                    first_page_text = ""
                    if doc_model.pages:
                        first_page_text = " ".join([p.text for p in doc_model.pages[0].paragraphs[:10] if p.text])
                    
                    from app.models.company import Company
                    companies = db.query(Company.name).all()
                    for (c_name,) in companies:
                        if c_name.lower() in first_page_text.lower() or c_name.lower() in file_name.lower():
                            company_name = c_name
                            break
                    
                    learned_context = ""
                    if getattr(settings, "USE_ENTERPRISE_LEARNING", False):
                        from app.services.learning_engine.learning_service import LearningService
                        learned_context = LearningService.get_learned_context(db, company_name)
                    
                    logger.info("USE_ENTERPRISE_LABELER is enabled. Running AI Field Labeling Engine...")
                    labeled_doc = FieldLabelingService.label_document(doc_model, learned_context=learned_context)

                chunks = DocxSegmenterService.segment_docx(file_bytes, file_name)
                
                # Parse and save page-by-page
                for chunk in chunks:
                    try:
                        logger.info(f"Parsing page {chunk.page_number}/{len(chunks)} of {file_name}")
                        
                        if settings.USE_ENTERPRISE_LABELER and labeled_doc:
                            from app.services.field_labeling import LabeledDocument
                            page_elements = [el for el in labeled_doc.elements if el.coordinates.get("page_number") == chunk.page_number]
                            page_labeled_doc = LabeledDocument(metadata=labeled_doc.metadata, elements=page_elements)
                            extracted_dict = FieldLabelingService.map_to_parser_dict(page_labeled_doc)
                            bill_res = AiExtractionService.map_to_bill_response(extracted_dict, chunk.raw_text)
                            bill_res.labeledDocument = page_labeled_doc.to_json()

                            if settings.USE_ENTERPRISE_VALIDATION:
                                from app.services.validation_engine import ValidationEngineService
                                logger.info("USE_ENTERPRISE_VALIDATION is enabled. Running Validation Engine...")
                                validation_doc = ValidationEngineService.validate_labeled_document(db, page_labeled_doc)
                                bill_res.validationReport = validation_doc.to_json()

                                # Propagate validation engine issues as warnings
                                validation_warnings = [f"[{iss.severity}] {iss.message}" for iss in validation_doc.issues]
                                if bill_res.warnings:
                                    bill_res.warnings.extend(validation_warnings)
                                else:
                                    bill_res.warnings = validation_warnings
                        else:
                            rag_context = BulkImportService._index_and_retrieve_rag_context(chunk.raw_text, file_name, chunk.page_number)
                            extracted_dict = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name, rag_context=rag_context)
                            bill_res = AiExtractionService.map_to_bill_response(extracted_dict, chunk.raw_text)

                        bill_res.originalDoc = chunk.html_representation
                        bill_res.documentIntelligence = document_intelligence
                        
                        # Validate the bill
                        warnings = ValidationService.validate_bill(db, bill_res)
                        if bill_res.warnings:
                            for w in bill_res.warnings:
                                if w not in warnings:
                                    warnings.append(w)
                        
                        # Check critical validation issues (no slip number or no company name)
                        has_critical_error = any("Missing mandatory field" in w or "missing or zero" in w or "[ERROR]" in w for w in warnings)
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
                doc_model = DocumentIntelligenceService.extract_document(file_bytes, file_name)
                document_intelligence = doc_model.to_json()

                labeled_doc = None
                from app.config import settings
                if settings.USE_ENTERPRISE_LABELER:
                    from app.services.field_labeling import FieldLabelingService
                    
                    # Heuristic to detect company name from first page paragraphs or filename
                    company_name = None
                    first_page_text = ""
                    if doc_model.pages:
                        first_page_text = " ".join([p.text for p in doc_model.pages[0].paragraphs[:10] if p.text])
                    
                    from app.models.company import Company
                    companies = db.query(Company.name).all()
                    for (c_name,) in companies:
                        if c_name.lower() in first_page_text.lower() or c_name.lower() in file_name.lower():
                            company_name = c_name
                            break
                    
                    learned_context = ""
                    if getattr(settings, "USE_ENTERPRISE_LEARNING", False):
                        from app.services.learning_engine.learning_service import LearningService
                        learned_context = LearningService.get_learned_context(db, company_name)
                    
                    logger.info("USE_ENTERPRISE_LABELER is enabled. Running AI Field Labeling Engine for preview...")
                    labeled_doc = FieldLabelingService.label_document(doc_model, learned_context=learned_context)

                chunks = DocxSegmenterService.segment_docx(file_bytes, file_name)

                for chunk in chunks:
                    try:
                        logger.info(f"Parsing preview for page {chunk.page_number}/{len(chunks)}")
                        
                        if settings.USE_ENTERPRISE_LABELER and labeled_doc:
                            from app.services.field_labeling import LabeledDocument
                            page_elements = [el for el in labeled_doc.elements if el.coordinates.get("page_number") == chunk.page_number]
                            if page_elements:
                                page_labeled_doc = LabeledDocument(metadata=labeled_doc.metadata, elements=page_elements)
                                extracted_dict = FieldLabelingService.map_to_parser_dict(page_labeled_doc)
                            else:
                                extracted_dict = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name)
                                page_labeled_doc = None

                            # Merge per-chunk extraction fallback if critical fields are UNKNOWN or 0.0
                            chunk_extracted = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name)
                            for k, v in chunk_extracted.items():
                                if (not extracted_dict.get(k) or extracted_dict.get(k) == "UNKNOWN" or extracted_dict.get(k) in ["0.0", ""]) and v and v not in ["UNKNOWN", "0.0", ""]:
                                    extracted_dict[k] = v

                            bill_res = AiExtractionService.map_to_bill_response(extracted_dict, chunk.raw_text)
                            if page_labeled_doc:
                                bill_res.labeledDocument = page_labeled_doc.to_json()

                            if settings.USE_ENTERPRISE_VALIDATION and page_labeled_doc:
                                from app.services.validation_engine import ValidationEngineService
                                logger.info("USE_ENTERPRISE_VALIDATION is enabled. Running Validation Engine for preview...")
                                validation_doc = ValidationEngineService.validate_labeled_document(db, page_labeled_doc)
                                bill_res.validationReport = validation_doc.to_json()

                                validation_warnings = [f"[{iss.severity}] {iss.message}" for iss in validation_doc.issues]
                                if bill_res.warnings:
                                    bill_res.warnings.extend(validation_warnings)
                                else:
                                    bill_res.warnings = validation_warnings
                        else:
                            rag_context = BulkImportService._index_and_retrieve_rag_context(chunk.raw_text, file_name, chunk.page_number)
                            extracted_dict = AiExtractionService.extract_page_data(chunk.raw_text, filename=file_name, rag_context=rag_context)
                            bill_res = AiExtractionService.map_to_bill_response(extracted_dict, chunk.raw_text)

                        bill_res.originalDoc = chunk.html_representation
                        bill_res.documentIntelligence = document_intelligence
                        
                        # Validate and attach warnings
                        warnings = ValidationService.validate_bill(db, bill_res)
                        if bill_res.warnings:
                            for w in bill_res.warnings:
                                if w not in warnings:
                                    warnings.append(w)
                        bill_res.warnings = warnings
                        
                        all_parsed.append(bill_res)
                    except Exception as page_ex:
                        logger.error(f"Preview parsing failed for page {chunk.page_number} in {file_name}: {page_ex}")
            except Exception as e:
                logger.error(f"Failed to segment preview document {file_name}: {e}")
        return all_parsed
