# app/main.py
import logging
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from app.db.database import engine, Base
import redis
from celery import Celery

# -----------------------------
# Reduce SQLAlchemy logging noise
# -----------------------------
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

# -----------------------------
# FastAPI instance
# -----------------------------
app = FastAPI(title="EV Rental API 🚗")
from app.controllers.auth import signup


app.include_router(signup.router, prefix="/auth", tags=["Auth"])
# -----------------------------
# Singleton flags
# -----------------------------
db_initialized = False
redis_initialized = False
celery_initialized = False

# -----------------------------
# Global instances
# -----------------------------
redis_client: redis.Redis | None = None
celery_app: Celery | None = None

# -----------------------------
# Startup event
# -----------------------------
@app.on_event("startup")
def startup_event():
    global db_initialized, redis_initialized, celery_initialized
    global redis_client, celery_app

    # -------- Database --------
    if not db_initialized:
        try:
            print("🔗 Connecting to database...")
            Base.metadata.create_all(bind=engine)
            print("✅ Database connected and tables ready!")
            db_initialized = True
        except OperationalError as e:
            print("❌ Database connection failed:", e)

    # -------- Redis --------
    if not redis_initialized:
        try:
            print("🟢 Connecting to Redis...")
            redis_client = redis.Redis(host="localhost", port=6379, db=0)
            redis_client.ping()  # test connection
            print("✅ Redis connected!")
            redis_initialized = True
        except Exception as e:
            print("❌ Redis connection failed:", e)

    # -------- Celery --------
    if not celery_initialized:
        try:
            print("⚡ Initializing Celery...")
            celery_app = Celery(
                "ev_rental_tasks",
                broker="redis://localhost:6379/0",
                backend="redis://localhost:6379/0"
            )
            print("✅ Celery initialized!")
            celery_initialized = True
        except Exception as e:
            print("❌ Celery initialization failed:", e)

# -----------------------------
# Root endpoint
# -----------------------------
@app.get("/")
def root():
    return {"message": "EV Rental API running 🚀"}