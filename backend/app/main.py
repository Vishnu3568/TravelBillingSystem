import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.backups import backup_service

# Routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.companies import router as companies_router
from app.routers.vehicles import router as vehicles_router
from app.routers.bills import router as bills_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router
from app.routers.imports import router as imports_router
from app.routers.backups import router as backups_router
from app.routers.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Travel Billing System API",
    description="Python backend rewritten from Spring Boot using FastAPI",
    version="1.0.0"
)

# CORS configuration (Replicates Spring Security settings exactly)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # Standard way to allow credentials with wildcard-like pattern
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(vehicles_router)
app.include_router(bills_router)
app.include_router(audit_logs_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(imports_router)
app.include_router(backups_router)
app.include_router(dashboard_router)

# Scheduler for automated backups (replicates Spring Boot's @Scheduled(cron = "0 0 1 * * ?"))
def run_auto_backup():
    db = SessionLocal()
    try:
        logger.info("Starting automated daily backup...")
        backup_service.create_backup(db)
    except Exception as e:
        logger.error(f"Automated daily backup failed: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(run_auto_backup, 'cron', hour=1, minute=0)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database metadata...")
    # Replicates spring.jpa.hibernate.ddl-auto=update by creating tables/columns if missing
    Base.metadata.create_all(bind=engine)
    
    logger.info("Starting automated backup scheduler...")
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down automated backup scheduler...")
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "Travel Billing System Python API rewrite is up and running."}
