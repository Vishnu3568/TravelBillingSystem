import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal

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

@app.on_event("shutdown")
def on_shutdown():
    pass

@app.get("/")
def read_root():
    return {"message": "Travel Billing System Python API rewrite is up and running."}
