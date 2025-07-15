import os
from datetime import datetime

AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "audit.log")

def log_audit_event(user_identifier: str, event_type: str, details: str = ""):
    timestamp = datetime.utcnow().isoformat()
    log_line = f"{timestamp} | user={user_identifier} | event={event_type} | details={details}\n"
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(log_line) 