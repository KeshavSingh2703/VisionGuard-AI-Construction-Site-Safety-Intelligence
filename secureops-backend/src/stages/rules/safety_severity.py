from enum import Enum
from typing import List, Dict, Any


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def merge_safety_severity(
    ppe_violations: List[Dict[str, Any]],
    proximity_events: List[Dict[str, Any]],
) -> Severity:
    """
    Merge PPE + proximity signals into a final safety severity.
    
    Principles:
    - Proximity CRITICAL = Immediate CRITICAL
    - Proximity WARNING x2 = HIGH
    - PPE HIGH x1 = HIGH
    - PPE MEDIUM x2 = MEDIUM
    - Else LOW
    """

    # Immediate escalation rules (Proximity Critical dominates all)
    for event in proximity_events:
        if event.get("severity") == "CRITICAL":
            return Severity.CRITICAL

    # Count severities
    ppe_high = sum(1 for v in ppe_violations if v.get("severity") == "HIGH")
    ppe_medium = sum(1 for v in ppe_violations if v.get("severity") == "MEDIUM")

    proximity_warning = sum(
        1 for e in proximity_events if e.get("severity") == "WARNING"
    )

    # Escalation logic
    if proximity_warning >= 2:
        return Severity.HIGH

    if ppe_high >= 1:
        return Severity.HIGH

    if ppe_medium >= 2:
        return Severity.MEDIUM

    if ppe_violations or proximity_warning:
        return Severity.LOW

    return Severity.LOW
