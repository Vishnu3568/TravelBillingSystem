param (
    [string]$USER = "root",
    [string]$PASS = "root"
)
# Database Restore Script for Travel Billing System
$DB_NAME = "travelbillingdb"
$BACKUP_PATH = "../backups/travelbillingdb_dump.sql"


Write-Host "Restoring database $DB_NAME from $BACKUP_PATH..." -ForegroundColor Cyan

if (-Not (Test-Path $BACKUP_PATH)) {
    Write-Host "Backup file not found at $BACKUP_PATH" -ForegroundColor Red
    exit
}

# Create database if it doesn't exist
if ($PASS -eq "") {
    & mysql -u $USER -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
    # Import the SQL file using cmd.exe to handle redirection
    cmd.exe /c "mysql -u $USER $DB_NAME < `"$BACKUP_PATH`""
} else {
    & mysql -u $USER -p$PASS -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
    # Import the SQL file using cmd.exe to handle redirection
    cmd.exe /c "mysql -u $USER -p$PASS $DB_NAME < `"$BACKUP_PATH`""
}



if ($LASTEXITCODE -eq 0) {
    Write-Host "Restore successful!" -ForegroundColor Green
} else {
    Write-Host "Restore failed!" -ForegroundColor Red
}
