import os
import re
import subprocess
import logging
from datetime import datetime
from typing import List
from app.config import settings
from app.services.audit_log import AuditLogService
from app.schemas.backup import BackupResponse

logger = logging.getLogger("backup_service")

class BackupService:
    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        self._parse_db_url()

    def _parse_db_url(self):
        self.db_user = settings.DB_USERNAME
        self.db_pass = settings.DB_PASSWORD
        self.db_host = "localhost"
        self.db_port = "3306"
        self.db_name = "travelbillingdb"

        # Regex parsing to extract host/port details for mysqldump
        db_url = settings.sqlalchemy_database_url
        match = re.match(r"mysql\+pymysql://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([^?]+)", db_url)
        if match:
            self.db_user, self.db_pass, self.db_host, port, self.db_name = match.groups()
            self.db_port = port or "3306"

    def create_backup(self, db) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"backup_{timestamp}.sql"
        filepath = os.path.abspath(os.path.join(self.backup_dir, file_name))

        # Command construction (specifies host/port for containerized/remote execution)
        cmd = [
            "mysqldump",
            f"-h{self.db_host}",
            f"-P{self.db_port}",
            f"-u{self.db_user}",
            f"-p{self.db_pass}",
            "--databases",
            self.db_name,
            f"--result-file={filepath}"
        ]

        logger.info(f"Running backup command: mysqldump -h {self.db_host} -P {self.db_port} ...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Backup failed: {result.stderr}")
            raise IOError(f"Backup failed with exit code {result.returncode}: {result.stderr}")

        AuditLogService.log_action(
            db=db,
            action="BACKUP_CREATED",
            module="SYSTEM",
            description=f"Database backup created: {file_name}"
        )
        return file_name

    def restore_backup(self, db, file_bytes: bytes):
        import tempfile
        
        # Write bytes to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as temp_file:
            temp_file.write(file_bytes)
            temp_filepath = temp_file.name

        try:
            # Re-initialize DB using mysql client
            # We run source on the file
            cmd = [
                "mysql",
                f"-h{self.db_host}",
                f"-P{self.db_port}",
                f"-u{self.db_user}",
                f"-p{self.db_pass}",
                "-e",
                f"source {temp_filepath}"
            ]
            
            logger.info(f"Running restore command: mysql -h {self.db_host} -P {self.db_port} ...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                raise IOError(f"Restore failed with exit code {result.returncode}: {result.stderr}")

            AuditLogService.log_action(
                db=db,
                action="RESTORE_DONE",
                module="SYSTEM",
                description="Database restoration completed successfully from uploaded file"
            )
        finally:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    def get_history(self) -> List[BackupResponse]:
        if not os.path.exists(self.backup_dir):
            return []
            
        history = []
        for file in os.listdir(self.backup_dir):
            if file.endswith(".sql"):
                filepath = os.path.join(self.backup_dir, file)
                size = os.path.getsize(filepath)
                
                # Parse timestamp: backup_yyyyMMdd_HHmmss.sql
                created_at = datetime.now()
                try:
                    if len(file) >= 22:
                        ts_str = file[7:22]
                        created_at = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                except Exception:
                    pass
                    
                history.append(BackupResponse(
                    fileName=file,
                    size=size,
                    createdAt=created_at
                ))
                
        # Sort desc by createdAt
        history.sort(key=lambda x: x.createdAt, reverse=True)
        return history

    def get_backup_file(self, file_name: str) -> bytes:
        filepath = os.path.join(self.backup_dir, file_name)
        if not os.path.exists(filepath):
            raise FileNotFoundError("Backup file not found")
        with open(filepath, "rb") as f:
            return f.read()

    def delete_backup(self, db, file_name: str):
        filepath = os.path.join(self.backup_dir, file_name)
        if os.path.exists(filepath):
            os.remove(filepath)
            AuditLogService.log_action(
                db=db,
                action="DELETE_BACKUP",
                module="SYSTEM",
                description=f"Backup file deleted: {file_name}"
            )
        else:
            raise FileNotFoundError("Backup file not found")

backup_service = BackupService()
