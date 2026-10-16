import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Shorten connect timeout and keep connections healthy.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        # Quick connectivity check to fail fast instead of timing out.
        db.execute(text("SELECT 1"))
        yield db
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {exc}") from exc
    finally:
        try:
            db.close()
        except Exception:
            pass

