# app/main.py
import logging
import os
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from app.db.database import engine, Base
import redis
from celery import Celery
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware  # ✅ Import CORSMiddleware


# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USER = os.getenv("REDIS_USER", None)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_SSL = os.getenv("REDIS_SSL", "False").lower() in ("true", "1", "yes")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

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
################-----Routers------###############

from app.controllers.auth import signup
app.include_router(signup.router, prefix="/auth", tags=["Auth"])

from app.controllers.auth import signup, login
app.include_router(login.router, prefix="/auth", tags=["Auth"])

from app.controllers.auth import forgot_password
app.include_router(forgot_password.router)



from app.controllers.auth import change_password
app.include_router(change_password.router)

from app.controllers.Crud.read_users import router as read_users_router
app.include_router(read_users_router)

from app.controllers.admin import users 
app.include_router(users.router)

from app.controllers.auth import logout
app.include_router(logout.router)



from app.controllers.auth.get_user import router as get_user_router

app.include_router(get_user_router)

from app.controllers.user import userprofile

app.include_router(userprofile.router)

from app.controllers.user.userprofile import router as user_profile_router
from app.controllers.user.updateprofile import router as update_profile_router
from app.controllers.user.profilephotoupload import router as profile_photo_router

app.include_router(user_profile_router)
app.include_router(update_profile_router)
app.include_router(profile_photo_router)

from app.controllers.user.file_access import router as file_access_router

app.include_router(file_access_router)

from app.controllers.kyc.user_kyc_full import router as user_kyc_router
# CORS middleware for testing in Bruno
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the user KYC blueprint
app.include_router(user_kyc_router)

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
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                username=REDIS_USER,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                ssl=REDIS_SSL,
                decode_responses=True,
            )
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
                broker=CELERY_BROKER_URL,
                backend=CELERY_RESULT_BACKEND
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