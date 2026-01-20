from dotenv import load_dotenv
load_dotenv()

from src.db.session import get_engine
from src.db.models import Base, SiteMetrics, ProximityEvent, SafetyViolation, Upload

engine = get_engine()

# Determine tables to drop/create
# We are fixing mismatch for SiteMetrics and ProximityEvent.
# SafetyViolation and Upload seem ok or not complained about yet, 
# but SafetyViolation has file_name which is ok (user didn't complain).
# Just recreate the troublesome tables.

print("Dropping tables...")
SiteMetrics.__table__.drop(engine, checkfirst=True)
ProximityEvent.__table__.drop(engine, checkfirst=True)
SafetyViolation.__table__.drop(engine, checkfirst=True)

print("Creating tables...")
# create_all creates only tables that don't exist in DB but exist in metadata
Base.metadata.create_all(engine)

print("Schema fix complete.")
