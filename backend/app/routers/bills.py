import math
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.schemas.bill import BillRequest, BillResponse
from app.schemas.ai import AiBillResponse, AiSearchFilter
from app.services.bills import BillService
from app.services.pdf import PdfService
from app.utils.security import get_current_user, RoleChecker

router = APIRouter(prefix="/api/bills", tags=["bills"])

# Role guards
auth_guard = get_current_user
write_guard = RoleChecker(["OWNER", "MANAGER"])
delete_guard = RoleChecker(["OWNER"])

def make_page_response(content: list, total_elements: int, page: int, size: int) -> dict:
    total_pages = math.ceil(total_elements / size) if size > 0 else 0
    return {
        "content": content,
        "totalElements": total_elements,
        "totalPages": total_pages,
        "size": size,
        "number": page,
        "numberOfElements": len(content),
        "first": page == 0,
        "last": (page + 1) >= total_pages,
        "empty": len(content) == 0
    }

@router.post("", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(
    request_data: BillRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    bill = BillService.create_bill(db, request_data, current_user.get("sub"), ip)
    # Convert sqlalchemy model to response schema
    return BillResponse.model_validate(bill)

@router.post("/bulk", response_model=List[BillResponse], status_code=status.HTTP_201_CREATED)
def create_bills(
    request_data: List[BillRequest],
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    bills = BillService.save_bills(db, request_data, current_user.get("sub"), ip)
    return [BillResponse.model_validate(b) for b in bills]

@router.post("/bulk-ai", response_model=List[BillResponse], status_code=status.HTTP_201_CREATED)
def create_bills_ai(
    request_data: List[AiBillResponse],
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    bills = BillService.save_ai_parsed_bills(db, request_data, current_user.get("sub"), ip)
    return [BillResponse.model_validate(b) for b in bills]

@router.get("")
def get_bills(
    page: int = 0,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    items, total = BillService.get_bills(db, page, size)
    serialized = [BillResponse.model_validate(item).model_dump() for item in items]
    return make_page_response(serialized, total, page, size)

@router.get("/search")
def search_bills(
    billNumber: Optional[str] = None,
    companyName: Optional[str] = None,
    fromDate: Optional[date] = None,
    toDate: Optional[date] = None,
    page: int = 0,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    items, total = BillService.search_bills(db, bill_number=billNumber, company_name=companyName, from_date=fromDate, to_date=toDate, page=page, size=size)
    serialized = [BillResponse.model_validate(item).model_dump() for item in items]
    return make_page_response(serialized, total, page, size)

@router.get("/search/nl")
def search_bills_nl(
    query: str,
    page: int = 0,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    items, total = BillService.search_bills_nl(db, query, page, size)
    serialized = [BillResponse.model_validate(item).model_dump() for item in items]
    return make_page_response(serialized, total, page, size)

@router.get("/search/nl/explain", response_model=AiSearchFilter)
def explain_search_nl(
    query: str,
    current_user: dict = Depends(auth_guard)
):
    from app.services.gemini import gemini_service
    # Explains NL query by returning parsed search filter Pydantic model
    parsed = gemini_service.parse_search_query(query)
    if not parsed:
        return AiSearchFilter()
    return AiSearchFilter(**parsed)

@router.get("/export/csv")
def export_bills_csv(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """Generates and streams a CSV export of all bills."""
    import io
    import csv
    from app.models.bill import Bill

    bills = db.query(Bill).order_by(Bill.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Bill Number", "Bill Date", "Company", "Vehicle",
        "Duty Slip", "Total KMs", "Total Hours", "Grand Total", "Created By"
    ])

    for b in bills:
        writer.writerow([
            b.id,
            b.bill_number or "",
            b.bill_date.isoformat() if b.bill_date else "",
            b.company_name or "",
            b.vehicle_name or "",
            b.duty_slip_no or "",
            b.total_kms or 0.0,
            b.total_hours or 0.0,
            b.grand_total or 0.0,
            b.created_by or "",
        ])

    csv_content = output.getvalue()
    headers = {"Content-Disposition": 'attachment; filename="bills_export.csv"'}
    return Response(content=csv_content, media_type="text/csv", headers=headers)

@router.get("/export/summary")
def get_bills_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    """Returns aggregated summary metrics across all bills."""
    from sqlalchemy import func
    from app.models.bill import Bill

    total_count = db.query(func.count(Bill.id)).scalar() or 0
    total_amount = db.query(func.sum(Bill.grand_total)).scalar() or 0.0
    avg_amount = db.query(func.avg(Bill.grand_total)).scalar() or 0.0
    total_kms = db.query(func.sum(Bill.total_kms)).scalar() or 0.0

    return {
        "total_bills": total_count,
        "total_revenue": round(float(total_amount), 2),
        "average_bill_amount": round(float(avg_amount), 2),
        "total_kms_recorded": round(float(total_kms), 2),
    }

@router.get("/{id}", response_model=BillResponse)
def get_bill_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    from app.models.bill import Bill
    bill = db.query(Bill).filter(Bill.id == id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return BillResponse.model_validate(bill)

@router.get("/{id}/pdf")
def get_bill_pdf(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_guard)
):
    from app.models.bill import Bill
    bill = db.query(Bill).filter(Bill.id == id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
        
    pdf_content = PdfService.generate_invoice_pdf(db, id)
    
    headers = {
        "Content-Disposition": f'attachment; filename="Invoice-{bill.bill_number}.pdf"'
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

@router.put("/{id}", response_model=BillResponse)
def update_bill(
    id: int,
    request_data: BillRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(write_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    bill = BillService.update_bill(db, id, request_data, current_user.get("sub"), current_user.get("role"), ip)
    return BillResponse.model_validate(bill)

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_bills(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(delete_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    BillService.delete_all_bills(db, current_user.get("sub"), current_user.get("role"), ip)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(delete_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    BillService.delete_bill(db, id, current_user.get("sub"), current_user.get("role"), ip)
