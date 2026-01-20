from sqlalchemy import create_engine, text
from src.core.config import get_config
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

config = get_config()
db_url = f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}:{config.database.port}/{config.database.database}"

engine = create_engine(db_url)

print(f"\nConnected to: {config.database.database} @ {config.database.host}")
print("Fetching recent data...\n")

with engine.connect() as conn:
    print("=== RECENT SITE METRICS (Last 3) ===")
    result = conn.execute(text("SELECT upload_id, accuracy, ppe_violations, pipeline_status, created_at FROM site_metrics ORDER BY created_at DESC LIMIT 3"))
    for row in result:
        print(f"Time: {row.created_at} | Status: {row.pipeline_status} | Acc: {row.accuracy}% | Violations: {row.ppe_violations}")

    print("\n=== RECENT SAFETY VIOLATIONS (Last 5) ===")
    result = conn.execute(text("SELECT violation_type, severity, description, confidence FROM safety_violations ORDER BY detected_at DESC LIMIT 5"))
    for row in result:
        print(f"Type: {row.violation_type} | Sev: {row.severity} | Conf: {row.confidence:.2f} | Desc: {row.description}")

    print("\n=== RECENT PROXIMITY EVENTS (Last 3) ===")
    result = conn.execute(text("SELECT machine_type, distance_px, risk_level FROM proximity_events ORDER BY detected_at DESC LIMIT 3"))
    for row in result:
        print(f"Machine: {row.machine_type} | Dist: {row.distance_px:.1f}px | Risk: {row.risk_level}")
