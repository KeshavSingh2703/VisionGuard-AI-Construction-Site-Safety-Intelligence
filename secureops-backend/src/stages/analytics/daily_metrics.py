from typing import List, Dict, Any
from src.stages.aggregation.unified_stream import UnifiedViolation

class DailyMetricsEngine:
    """
    Computes daily safety metrics and risk scores from unified violation streams.
    """
    
    SEVERITY_WEIGHTS = {
        "safe": 0,
        "warning": 5,
        "critical": 10,
        "high": 10,    # Alias
        "medium": 5,   # Alias
        "low": 1       # Alias
    }

    def compute_metrics(self, stream: List[UnifiedViolation], total_frames: int = 0) -> Dict[str, Any]:
        """
        Compute metrics from a stream of violations.
        
        Args:
            stream: List of UnifiedViolation objects.
            total_frames: Total processed frames (for accuracy/frequency calc).
            
        Returns:
            Dictionary containing calculated metrics.
        """
        if not stream:
            return {
                "total_violations": 0,
                "ppe_violations": 0,
                "proximity_violations": 0,
                "zone_violations": 0,
                "risk_score": 0.0,
                "compliance_rate": 100.0,
                "most_frequent_violation": None
            }

        counts = {
            "ppe": 0,
            "proximity": 0,
            "zone": 0
        }
        
        raw_risk_score = 0
        
        for v in stream:
            # Count types
            if v.violation_type in counts:
                counts[v.violation_type] += 1
                
            # Accumulate Risk
            weight = self.SEVERITY_WEIGHTS.get(v.severity.lower(), 1)
            raw_risk_score += weight

        total_violations = len(stream)
        
        # Risk Score Formula: (Raw Score / (Total Events * Max Weight)) * 100
        # If total_violations is 0, handled above.
        # Max Weight is 10.
        # This gives a "Severity Density" score (0-100).
        max_possible_score = total_violations * 10
        risk_score = 0.0
        if max_possible_score > 0:
            risk_score = (raw_risk_score / max_possible_score) * 100
            
        # Compliance Rate
        # This is tricky without "total_people_detected".
        # Proxy: 100 - Risk Score? Or based on frame count?
        # Let's use the provided prompt's implication or standard logic.
        # "Compliance Rate" usually means % of safe observations.
        # Without safe observation counts, we can inverse risk or default to 100 - risk/2?
        # Let's stick to a simple inverse of risk score for now, or just 100 if no violations.
        # Actually, let's use: max(0, 100 - risk_score)
        compliance_rate = max(0.0, 100.0 - risk_score)
        
        return {
            "total_violations": total_violations,
            "ppe_violations": counts["ppe"],
            "proximity_violations": counts["proximity"],
            "zone_violations": counts["zone"],
            "risk_score": round(risk_score, 2),
            "compliance_rate": round(compliance_rate, 2),
        }
