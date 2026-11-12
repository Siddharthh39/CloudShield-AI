import json
import urllib.request

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.database import DATABASE_URL
from Backend.models import Base
from Backend.seed_data import seed_demo_data


def _send(event, context, status, data, reason=None):
    body = json.dumps({
        "Status": status,
        "Reason": reason or f"See CloudWatch log stream: {context.log_stream_name}",
        "PhysicalResourceId": event.get("PhysicalResourceId", context.log_stream_name),
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data,
    }).encode()
    request = urllib.request.Request(event["ResponseURL"], data=body, method="PUT")
    request.add_header("content-type", "")
    request.add_header("content-length", str(len(body)))
    with urllib.request.urlopen(request, timeout=10):
        return None


def handler(event, context):
    try:
        if event["RequestType"] != "Delete":
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
            Base.metadata.create_all(engine)
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    "ALTER TABLE monitored_sites ADD COLUMN IF NOT EXISTS owner_sub VARCHAR"
                )
                connection.exec_driver_sql(
                    "ALTER TABLE monitored_sites ADD COLUMN IF NOT EXISTS approval_status VARCHAR NOT NULL DEFAULT 'approved'"
                )
            seed_demo_data(sessionmaker(bind=engine)())
        _send(event, context, "SUCCESS", {"seeded": event["RequestType"] != "Delete"})
    except Exception as exc:
        _send(event, context, "FAILED", {}, str(exc))
        raise
    return {"status": "ok"}
