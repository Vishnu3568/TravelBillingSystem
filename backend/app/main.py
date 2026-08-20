import logging
import sys
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, SessionLocal, get_db

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
from app.routers.dashboard import router as dashboard_router
from app.routers.learning import router as learning_router
from app.services.enterprise_copilot.copilot_router import router as copilot_router
from app.routers.graph import router as graph_router
from app.routers.predictive import router as predictive_router
from app.routers.amip_monitoring import router as amip_monitoring_router
from app.routers.amip_workflow import router as amip_workflow_router

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
app.include_router(dashboard_router)
app.include_router(learning_router)
app.include_router(copilot_router)
app.include_router(graph_router)
app.include_router(predictive_router)
app.include_router(amip_monitoring_router)
app.include_router(amip_workflow_router)


@app.on_event("startup")
def on_startup():
    logger.info("Initializing database metadata...")
    # Replicates spring.jpa.hibernate.ddl-auto=update by creating tables/columns if missing
    Base.metadata.create_all(bind=engine)
    
    # Seed default owner user if not present
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.utils.security import hash_password
        owner_exists = db.query(User).filter(User.username == "owner2").first()
        if not owner_exists:
            logger.info("Seeding default owner user 'owner2'...")
            new_owner = User(
                username="owner2",
                password_hash=hash_password("admin123"),
                email="owner2@test.com",
                role="OWNER",
                active=True
            )
            db.add(new_owner)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to seed default owner: {e}")
    finally:
        db.close()

    # Startup Self Test & Verification Report
    logger.info("==================================================")
    logger.info("       STARTUP SELF TEST & CONFIGURATION REPORT   ")
    logger.info("==================================================")

    # Check Database
    db_ok = "OK"
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_ok = f"FAILED: {e}"
    logger.info(f"Database Connection:        {db_ok}")

    # Check Configuration & Flags
    logger.info(f"USE_ENTERPRISE_LEARNING:    {settings.USE_ENTERPRISE_LEARNING}")
    logger.info(f"USE_ENTERPRISE_COPILOT:     {settings.USE_ENTERPRISE_COPILOT}")
    logger.info(f"USE_ENTERPRISE_GRAPH:       {settings.USE_ENTERPRISE_GRAPH}")
    logger.info(f"USE_PREDICTIVE_ENGINE:      {settings.USE_PREDICTIVE_ENGINE}")
    logger.info(f"GEMINI_MODEL:               {settings.GEMINI_MODEL or 'gemini-1.5-pro (default)'}")

    # ----------------------------------------------------------------
    # Gemini API Key validation
    # In DEVELOPMENT: missing / placeholder key -> warn and disable AI
    # features gracefully. Server ALWAYS boots.
    # ----------------------------------------------------------------
    _KNOWN_PLACEHOLDERS = {
        "",
    }
    gemini_key_valid = (
        bool(settings.GEMINI_API_KEY)
        and settings.GEMINI_API_KEY not in _KNOWN_PLACEHOLDERS
        and not settings.GEMINI_API_KEY.startswith("YOUR_")
        and not settings.GEMINI_API_KEY.startswith("your_")
    )

    if gemini_key_valid:
        gemini_key_ok = "SET (valid)"
    else:
        gemini_key_ok = "MISSING or PLACEHOLDER — AI features disabled"
        # Disable every AI-dependent feature flag at runtime so endpoints
        # return descriptive errors instead of crashing at startup.
        settings.USE_ENTERPRISE_LEARNING = False
        settings.USE_ENTERPRISE_COPILOT = False
        settings.USE_ENTERPRISE_GRAPH = False
        settings.USE_PREDICTIVE_ENGINE = False
        settings.USE_ENTERPRISE_LABELER = False
        settings.USE_ENTERPRISE_VALIDATION = False

    logger.info(f"Gemini API Key:             {gemini_key_ok}")
    internal_key_ok = "SET" if settings.INTERNAL_API_KEY else "USING DEFAULT LOCAL KEY"
    logger.info(f"Internal API Key:           {internal_key_ok}")
    logger.info("==================================================")

    # ----------------------------------------------------------------
    # Database enforcement
    # In PRODUCTION (ENV != dev): hard exit if DB is unreachable.
    # In DEVELOPMENT: log an error and continue (avoids blocking local
    # development when MySQL is not yet running).
    # ----------------------------------------------------------------
    if db_ok != "OK":
        if not settings.is_dev:
            logger.error(f"STARTUP FAILED: Database unavailable in production: {db_ok}")
            sys.exit(1)
        else:
            logger.error(
                f"Database connection FAILED: {db_ok}\n"
                "  Running in DEV mode — server will start but DB-dependent"
                " endpoints will return errors. Start MySQL to resolve."
            )

    if not gemini_key_valid:
        logger.warning(
            "\n"
            "  ====================================================\n"
            "  WARNING: GEMINI_API_KEY is missing or is a placeholder.\n"
            "  AI-dependent features (Learning, Copilot, Graph,\n"
            "  Predictive, Labeler, Validation) are DISABLED.\n"
            "  Set a valid GEMINI_API_KEY in backend/.env to enable.\n"
            "  ===================================================="
        )

@app.on_event("shutdown")
def on_shutdown():
    pass

@app.get("/")
def read_root():
    return {"message": "Travel Billing System Python API rewrite is up and running."}

@app.get("/api/health")
def api_health(db: Session = Depends(get_db)):
    health_status = {
        "status": "UP",
        "node_server": "DOWN",
        "python_server_rag": "DOWN",
        "gemini": "DOWN",
        "embeddings": "DOWN",
        "vector_store": "DOWN",
        "knowledge_graph": "DOWN",
        "predictive_engine": "DOWN",
        "learning_engine": "DOWN",
        "database": "DOWN"
    }

    # 1. Database Connection check
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["database"] = "UP"
    except Exception as e:
        health_status["database"] = f"DOWN: {e}"
        health_status["status"] = "DOWN"

    # 2. Node server check
    import requests
    headers = {"x-api-key": settings.INTERNAL_API_KEY or "travel_billing_secret_token_123"}
    try:
        res = requests.get("http://localhost:9001/health", headers=headers, timeout=1.0)
        if res.status_code == 200:
            health_status["node_server"] = "UP"
            health_status["gemini"] = "UP" if settings.GEMINI_API_KEY else "DOWN"
            health_status["embeddings"] = "UP" if settings.GEMINI_API_KEY else "DOWN"
            health_status["vector_store"] = "UP"
    except Exception as e:
        health_status["node_server"] = f"DOWN: {e}"
        if health_status["status"] == "UP":
            health_status["status"] = "DEGRADED"

    # 3. Python RAG server check
    try:
        res_rag = requests.get("http://localhost:9002/", timeout=1.0)
        if res_rag.status_code in (200, 404):
            health_status["python_server_rag"] = "UP"
    except Exception:
        health_status["python_server_rag"] = "DOWN"

    # 4. Feature flags checks
    health_status["knowledge_graph"] = "UP (Active)" if settings.USE_ENTERPRISE_GRAPH else "OFF (Disabled)"
    health_status["predictive_engine"] = "UP (Active)" if settings.USE_PREDICTIVE_ENGINE else "OFF (Disabled)"
    health_status["learning_engine"] = "UP (Active)" if settings.USE_ENTERPRISE_LEARNING else "OFF (Disabled)"

    return health_status
