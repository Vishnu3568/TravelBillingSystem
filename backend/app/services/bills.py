import json
import random
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException, status
from app.models.bill import Bill
from app.models.company import Company
from app.models.vehicle import Vehicle
from app.schemas.bill import BillRequest
from app.schemas.ai import AiBillResponse
from app.services.audit_log import AuditLogService
from app.services.gemini import gemini_service

logger = logging.getLogger("bill_service")

def parse_any_date(date_str: str) -> date:
    if not date_str or str(date_str).strip() in ["", "---", "UNKNOWN"]:
        return date.today()
    cleaned = str(date_str).strip()
    
    # Try YYYY-MM-DD
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        pass
        
    # Try DD-MM-YYYY
    try:
        return datetime.strptime(cleaned, "%d-%m-%Y").date()
    except ValueError:
        pass
        
    # Try DD-MM-YY
    try:
        return datetime.strptime(cleaned, "%d-%m-%y").date()
    except ValueError:
        pass
        
    # Try YYYY/MM/DD
    try:
        return datetime.strptime(cleaned, "%Y/%m/%d").date()
    except ValueError:
        pass
        
    # Try DD/MM/YYYY
    try:
        return datetime.strptime(cleaned, "%d/%m/%Y").date()
    except ValueError:
        pass
        
    # Fallback to finding digits
    import re
    match = re.findall(r'\d+', cleaned)
    if len(match) >= 3:
        try:
            if len(match[0]) == 4:
                return date(int(match[0]), int(match[1]), int(match[2]))
            else:
                year = int(match[2])
                if year < 100:
                    year += 2000
                return date(year, int(match[1]), int(match[0]))
        except Exception:
            pass
            
    return date.today()

class BillService:
    @staticmethod
    def create_bill(db: Session, request: BillRequest, created_by: str, ip: str) -> Bill:
        grand_total = BillService._calculate_grand_total(request)
        bill_datetime = datetime.combine(request.billDate, datetime.min.time())

        # Data Integrity: Find or create company
        company = None
        comp_name = request.companyName.strip() if request.companyName else ""
        if comp_name:
            company = db.query(Company).filter(Company.name == comp_name).first()
            if not company:
                company = Company(name=comp_name, address="Imported via AI")
                db.add(company)
                db.commit()
                db.refresh(company)

        # Data Integrity: Find or create vehicle
        vehicle = None
        veh_name = request.vehicleName.strip() if request.vehicleName else ""
        if veh_name:
            vehicle = db.query(Vehicle).filter(Vehicle.registration_number == veh_name).first()
            if not vehicle:
                veh_type = request.vehicleType if request.vehicleType else "Car"
                vehicle = Vehicle(registration_number=veh_name, type=veh_type)
                db.add(vehicle)
                db.commit()
                db.refresh(vehicle)

        # Generate unique bill number
        bill_number = BillService._generate_bill_number(db)

        trip_datetime = datetime.combine(request.tripDate, datetime.min.time()) if request.tripDate else None

        # Build Bill
        bill = Bill(
            bill_number=bill_number,
            amount=grand_total,
            bill_date=bill_datetime,
            company_name=comp_name,
            vehicle_name=veh_name,
            duty_slip_no=request.dutySlipNo.strip() if request.dutySlipNo else "",
            trip_date=trip_datetime,
            vehicle_type=request.vehicleType,
            ac_non_ac=request.acNonAc,
            total_kms=request.totalKms or 0.0,
            total_hours=request.totalHours or 0.0,
            extra_kms=request.extraKms or 0.0,
            extra_hours=request.extraHours or 0.0,
            trip_type=request.tripType,
            pricing_type=request.pricingType,
            notes=request.notes,
            dynamic_charges=BillService._serialize_charges(request.dynamicCharges),
            grand_total=grand_total,
            created_by=created_by,
            company_id=company.id if company else None,
            vehicle_id=vehicle.id if vehicle else None,
            contact_person=request.contactPerson,
            booked_by=request.bookedBy,
            manager_name=request.managerName,
            raw_values=request.rawValues,
            original_doc=request.originalDoc
        )
        
        BillService._populate_hardcoded_fields(bill, request)
        
        db.add(bill)
        db.commit()
        db.refresh(bill)

        # Log creation
        AuditLogService.log_action(
            db=db,
            action="CREATE_BILL",
            module="BILL",
            description=f"Bill {bill.bill_number} created for {bill.company_name}",
            username=created_by,
            role="USER",
            ip_address=ip
        )

        # Async index in AI (using try-except in case AI service fails)
        try:
            gemini_service.index_bill(bill.id, BillService._format_bill_text(bill))
        except Exception as e:
            logger.warning(f"Failed to index bill #{bill.id} on create: {e}")

        return bill

    @staticmethod
    def save_bills(db: Session, requests: List[BillRequest], created_by: str, ip: str) -> List[Bill]:
        saved_bills = []
        for req in requests:
            saved_bills.append(BillService.create_bill(db, req, created_by, ip))
        return saved_bills

    @staticmethod
    def save_ai_parsed_bills(db: Session, ai_responses: List[AiBillResponse], created_by: str, ip: str) -> List[Bill]:
        saved_bills = []
        for ai in ai_responses:
            try:
                # Map AI response back to BillRequest
                def sf(val) -> float:
                    if val is None or val == "":
                        return 0.0
                    try:
                        return float(val)
                    except Exception:
                        import re
                        match = re.search(r'[\d\.]+', str(val))
                        if match:
                            try:
                                return float(match.group(0))
                            except Exception:
                                pass
                    return 0.0

                req_data = {
                    "companyName": ai.companyName or "Unknown Company",
                    "vehicleName": ai.vehicleNumber or "Unknown Vehicle",
                    "vehicleType": ai.vehicleType or "Car",
                    "totalKms": sf(ai.totalKms),
                    "totalHours": sf(ai.totalHours),
                    "extraKms": sf(ai.extraKms),
                    "extraHours": sf(ai.extraHours),
                    "baseAmount": sf(ai.baseAmount) if ai.baseAmount else sf(ai.totalAmount),
                    "driverBata": sf(ai.driverBata),
                    "parking": sf(ai.parking),
                    "toll": sf(ai.toll),
                    "nightCharges": sf(ai.nightCharges),
                    "otherCharges": sf(ai.otherCharges),
                    "tripType": "Outstation",
                    "pricingType": "BASE"
                }

                # Duty slip check/generation
                if not ai.dutySlipNo or ai.dutySlipNo.strip() == "" or ai.dutySlipNo == "---":
                    import time
                    req_data["dutySlipNo"] = f"AI-{int(time.time()) % 10000}"
                else:
                    req_data["dutySlipNo"] = ai.dutySlipNo.strip()

                # Duplicate validation (exact duplicate skip matches Java)
                exists = db.query(Bill).filter(
                    Bill.duty_slip_no == req_data["dutySlipNo"],
                    Bill.company_name == req_data["companyName"]
                ).first()
                if exists:
                    logger.info(f"Duplicate AI bill skipped: {req_data['dutySlipNo']} for company {req_data['companyName']}")
                    continue

                # Bill date parsing
                req_data["billDate"] = parse_any_date(ai.billDate)

                # Trip date parsing
                req_data["tripDate"] = parse_any_date(ai.tripDate) if ai.tripDate else req_data["billDate"]

                # Contact person (Guest) and Booked by
                req_data["contactPerson"] = ai.contactPerson
                req_data["bookedBy"] = ai.bookedBy

                # Dynamic charges mapping
                dynamic = []
                if ai.dynamicCharges:
                    for c in ai.dynamicCharges:
                        dynamic.append({"name": c.name, "amount": c.amount})
                        name_lower = c.name.lower()
                        if "toll" in name_lower:
                            req_data["toll"] = c.amount
                        elif "parking" in name_lower:
                            req_data["parking"] = c.amount
                        elif "driver" in name_lower or "bata" in name_lower:
                            req_data["driverBata"] = c.amount
                        elif "night" in name_lower:
                            req_data["nightCharges"] = c.amount

                req_data["dynamicCharges"] = dynamic
                req_data["rawValues"] = ai.rawValues
                req_data["originalDoc"] = ai.originalDoc
                
                request_obj = BillRequest(**req_data)
                saved_bills.append(BillService.create_bill(db, request_obj, created_by, ip))
            except Exception as e:
                logger.error(f"Failed to save individual AI bill: {getattr(ai, 'dutySlipNo', 'N/A')}. Error: {e}")

        return saved_bills

    @staticmethod
    def update_bill(db: Session, bill_id: int, request: BillRequest, current_user: str, current_role: str, ip: str) -> Bill:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")

        grand_total = BillService._calculate_grand_total(request)
        bill_datetime = datetime.combine(request.billDate, datetime.min.time())

        # Update properties
        bill.bill_date = bill_datetime
        bill.company_name = request.companyName.strip()
        bill.vehicle_name = request.vehicleName.strip()
        bill.duty_slip_no = request.dutySlipNo.strip()
        bill.trip_date = datetime.combine(request.tripDate, datetime.min.time()) if request.tripDate else None
        bill.vehicle_type = request.vehicleType
        bill.ac_non_ac = request.acNonAc
        bill.total_kms = request.totalKms or 0.0
        bill.total_hours = request.totalHours or 0.0
        bill.extra_kms = request.extraKms or 0.0
        bill.extra_hours = request.extraHours or 0.0
        bill.trip_type = request.tripType
        bill.pricing_type = request.pricingType
        bill.notes = request.notes
        bill.dynamic_charges = BillService._serialize_charges(request.dynamicCharges)
        bill.grand_total = grand_total
        bill.contact_person = request.contactPerson
        bill.booked_by = request.bookedBy
        bill.manager_name = request.managerName
        if request.rawValues is not None:
            bill.raw_values = request.rawValues
        if request.originalDoc is not None:
            bill.original_doc = request.originalDoc

        BillService._populate_hardcoded_fields(bill, request)
        db.commit()
        db.refresh(bill)

        # Log action
        AuditLogService.log_action(
            db=db,
            action="UPDATE_BILL",
            module="BILL",
            description=f"Bill {bill.bill_number} updated",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

        try:
            gemini_service.index_bill(bill.id, BillService._format_bill_text(bill))
        except Exception as e:
            logger.warning(f"Failed to index bill #{bill.id} on update: {e}")

        return bill

    @staticmethod
    def delete_bill(db: Session, bill_id: int, current_user: str, current_role: str, ip: str):
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")

        bill_number = bill.bill_number
        db.delete(bill)
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="DELETE_BILL",
            module="BILL",
            description=f"Bill {bill_number} deleted",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

    @staticmethod
    def delete_all_bills(db: Session, current_user: str, current_role: str, ip: str):
        db.query(Bill).delete()
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="DELETE_ALL_BILLS",
            module="BILL",
            description="All bills deleted from database",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

    @staticmethod
    def get_bills(db: Session, page: int, size: int) -> Tuple[List[Bill], int]:
        query = db.query(Bill).order_by(Bill.created_at.desc())
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        return items, total

    @staticmethod
    def search_bills(
        db: Session,
        bill_number: str = None,
        company_name: str = None,
        from_date: date = None,
        to_date: date = None,
        page: int = 0,
        size: int = 10
    ) -> Tuple[List[Bill], int]:
        query = db.query(Bill)
        
        if bill_number and bill_number.strip():
            query = query.filter(Bill.bill_number.like(f"%{bill_number.strip()}%"))
        if company_name and company_name.strip():
            query = query.filter(Bill.company_name.like(f"%{company_name.strip()}%"))
        if from_date:
            from_dt = datetime.combine(from_date, datetime.min.time())
            query = query.filter(Bill.bill_date >= from_dt)
        if to_date:
            to_dt = datetime.combine(to_date, datetime.max.time())
            query = query.filter(Bill.bill_date <= to_dt)

        query = query.order_by(Bill.bill_date.desc())
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        return items, total

    @staticmethod
    def search_bills_nl(db: Session, query_text: str, page: int, size: int) -> Tuple[List[Bill], int]:
        filter_dict = gemini_service.parse_search_query(query_text)
        if not filter_dict:
            return BillService.search_bills(db, page=page, size=size)

        query = db.query(Bill)

        # Apply parsed parameters
        comp_name = filter_dict.get("companyName")
        if comp_name and comp_name.strip():
            query = query.filter(Bill.company_name.like(f"%{comp_name.strip()}%"))

        veh_type = filter_dict.get("vehicleType")
        if veh_type and veh_type.strip():
            query = query.filter(Bill.vehicle_type.like(f"%{veh_type.strip()}%"))

        min_amt = filter_dict.get("minAmount")
        if min_amt is not None:
            query = query.filter(Bill.grand_total >= min_amt)

        max_amt = filter_dict.get("maxAmount")
        if max_amt is not None:
            query = query.filter(Bill.grand_total <= max_amt)

        min_km = filter_dict.get("minKm")
        if min_km is not None:
            query = query.filter(Bill.total_kms >= min_km)

        max_km = filter_dict.get("maxKm")
        if max_km is not None:
            query = query.filter(Bill.total_kms <= max_km)

        # Date boundaries
        date_from = filter_dict.get("dateFrom")
        if date_from:
            try:
                from_dt = datetime.combine(date.fromisoformat(date_from), datetime.min.time())
                query = query.filter(Bill.bill_date >= from_dt)
            except Exception:
                pass

        date_to = filter_dict.get("dateTo")
        if date_to:
            try:
                to_dt = datetime.combine(date.fromisoformat(date_to), datetime.max.time())
                query = query.filter(Bill.bill_date <= to_dt)
            except Exception:
                pass

        # Keywords search
        keywords = filter_dict.get("keywords")
        if keywords:
            keyword_predicates = []
            for kw in keywords:
                keyword_predicates.append(Bill.notes.like(f"%{kw}%"))
                keyword_predicates.append(Bill.bill_number.like(f"%{kw}%"))
            query = query.filter(or_(*keyword_predicates))

        query = query.order_by(Bill.bill_date.desc())
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        return items, total

    @staticmethod
    def _calculate_grand_total(request: BillRequest) -> float:
        total = request.baseAmount or 0.0
        if request.dynamicCharges:
            for charge in request.dynamicCharges:
                total += charge.amount or 0.0
        else:
            total += (request.driverBata or 0.0) + \
                     (request.parking or 0.0) + \
                     (request.toll or 0.0) + \
                     (request.nightCharges or 0.0) + \
                     (request.otherCharges or 0.0)
        return total

    @staticmethod
    def _populate_hardcoded_fields(bill: Bill, request: BillRequest):
        if request.dynamicCharges:
            # Clear first (matches Java behaviour)
            bill.base_amount = 0.0
            bill.driver_bata = 0.0
            bill.parking = 0.0
            bill.toll = 0.0
            bill.night_charges = 0.0
            bill.other_charges = 0.0

            for charge in request.dynamicCharges:
                if not charge.name:
                    continue
                name = charge.name.strip().lower()
                amount = charge.amount or 0.0
                
                if "base" in name:
                    bill.base_amount = amount
                elif "bata" in name or "driver" in name:
                    bill.driver_bata = amount
                elif "parking" in name:
                    bill.parking = amount
                elif "toll" in name:
                    bill.toll = amount
                elif "night" in name:
                    bill.night_charges = amount
                elif "other" in name:
                    bill.other_charges = amount
        else:
            bill.base_amount = request.baseAmount or 0.0
            bill.driver_bata = request.driverBata or 0.0
            bill.parking = request.parking or 0.0
            bill.toll = request.toll or 0.0
            bill.night_charges = request.nightCharges or 0.0
            bill.other_charges = request.otherCharges or 0.0

    @staticmethod
    def _generate_bill_number(db: Session) -> str:
        date_str = date.today().strftime("%Y%m%d")
        prefix = f"BILL-{date_str}-"
        
        while True:
            rand_num = f"{random.randint(0, 9999):04d}"
            bill_number = f"{prefix}{rand_num}"
            # Check uniqueness
            exists = db.query(Bill).filter(Bill.bill_number == bill_number).first()
            if not exists:
                return bill_number

    @staticmethod
    def _serialize_charges(charges: List[Any]) -> str:
        if not charges:
            return "[]"
        try:
            # Convert list of schemas to dictionaries
            charges_dicts = []
            for c in charges:
                if hasattr(c, "model_dump"):
                    charges_dicts.append(c.model_dump())
                else:
                    charges_dicts.append(c)
            return json.dumps(charges_dicts)
        except Exception as e:
            logger.error(f"Error serializing charges: {e}")
            return "[]"

    @staticmethod
    def _format_bill_text(bill: Bill) -> str:
        return f"Bill Number: {bill.bill_number}, Date: {bill.bill_date.date() if bill.bill_date else 'N/A'}, Company: {bill.company_name}, Vehicle: {bill.vehicle_name} ({bill.vehicle_type or 'N/A'}), KMS: {bill.total_kms or 0.0}, Hours: {bill.total_hours or 0.0}, Total Amount: {bill.grand_total or 0.0:.2f}, Notes: {bill.notes or ''}"
