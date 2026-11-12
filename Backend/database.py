import os
import json
from urllib.parse import quote_plus

import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL and os.getenv("DB_SECRET_ARN"):
    secret = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION")).get_secret_value(
        SecretId=os.environ["DB_SECRET_ARN"]
    )
    credentials = json.loads(secret["SecretString"])
    database_name = os.getenv("DB_NAME", "cloudshield")
    host = os.environ["DB_HOST"]
    DATABASE_URL = (
        f"postgresql+psycopg2://{quote_plus(credentials['username'])}:"
        f"{quote_plus(credentials['password'])}@{host}:5432/{database_name}"
    )

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
    db = None
    try:
        db = SessionLocal()
        # Quick connectivity check to fail fast instead of timing out.
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {exc}") from exc
    try:
        yield db
    finally:
        if db is not None:
            db.close()
