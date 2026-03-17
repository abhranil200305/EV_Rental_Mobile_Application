# app/main.py
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from app.db.database import engine, Base  # ✅ updated import path

app = FastAPI(title="EV Rental API 🚗")

# Test DB connection on startup
@app.on_event("startup")
def startup_event():
    try:
        print("🔗 Connecting to database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected and tables ready!")
    except OperationalError as e:
        print("❌ Database connection failed:", e)

@app.get("/")
def root():
    return {"message": "EV Rental API running 🚀"}