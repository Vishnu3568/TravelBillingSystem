from fastapi import APIRouter, Depends, Request, Response, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.backup import BackupResponse
from app.services.backups import backup_service
from app.utils.security import RoleChecker

router = APIRouter(prefix="/api/backup", tags=["backup"])

owner_guard = RoleChecker(["OWNER"])

@router.post("/create", response_model=str)
def create_backup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    try:
        file_name = backup_service.create_backup(db)
        return f"Backup created successfully: {file_name}"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )

@router.post("/restore", response_model=str)
async def restore_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    try:
        content = await file.read()
        backup_service.restore_backup(db, content)
        return "Database restored successfully"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )

@router.get("/history", response_model=List[BackupResponse])
def get_history(
    current_user: dict = Depends(owner_guard)
):
    return backup_service.get_history()

@router.get("/download/{fileName}")
def download_backup(
    fileName: str,
    current_user: dict = Depends(owner_guard)
):
    try:
        data = backup_service.get_backup_file(fileName)
        headers = {
            "Content-Disposition": f"attachment; filename={fileName}"
        }
        return Response(content=data, media_type="application/octet-stream", headers=headers)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{fileName}", status_code=status.HTTP_200_OK)
def delete_backup(
    fileName: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(owner_guard)
):
    try:
        backup_service.delete_backup(db, fileName)
        return {"message": "Backup file deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
