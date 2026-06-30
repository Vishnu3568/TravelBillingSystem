from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.imports import BulkImportService
from app.utils.security import RoleChecker

from app.schemas.ai import AiBillResponse

router = APIRouter(prefix="/api/import", tags=["import"])

owner_guard = RoleChecker(["OWNER"])
manager_guard = RoleChecker(["OWNER", "MANAGER"])

@router.post("/ai-parse", response_model=List[AiBillResponse])
async def ai_parse(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(owner_guard)
):
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({
            "filename": f.filename,
            "content": content
        })
        
    return BulkImportService.parse_bills_only(files_data)


@router.post("/bills")
async def import_bills(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({
            "filename": f.filename,
            "content": content
        })
        
    return BulkImportService.import_bills(
        db=db, 
        files=files_data, 
        created_by=current_user.get("sub"), 
        ip=ip
    )

@router.post("/companies")
async def import_companies(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(manager_guard)
):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({
            "filename": f.filename,
            "content": content
        })
        
    return BulkImportService.import_companies(
        db=db,
        files=files_data,
        current_user=current_user.get("sub"),
        current_role=current_user.get("role"),
        ip=ip
    )
