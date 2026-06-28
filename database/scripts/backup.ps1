param (
    [string]$USER = "root",
    [string]$PASS = "root"
)
# Database Backup Script for Travel Billing System
$DB_NAME = "travelbillingdb"
$BACKUP_PATH = "../backups/travelbillingdb_dump.sql"


Write-Host "Backing up database $DB_NAME to $BACKUP_PATH..." -ForegroundColor Cyan

# Use mysqldump to export the database
if ($PASS -eq "") {
    & mysqldump -u $USER $DB_NAME --result-file=$BACKUP_PATH
} else {
    & mysqldump -u $USER -p$PASS $DB_NAME --result-file=$BACKUP_PATH
}


if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup successful!" -ForegroundColor Green
} else {
    Write-Host "Backup failed!" -ForegroundColor Red
}
