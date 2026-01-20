import pytest
from src.stages.rules.safety_severity import merge_safety_severity, Severity

def test_proximity_critical_dominates():
    ppe = []
    prox = [{"severity": "CRITICAL"}]
    assert merge_safety_severity(ppe, prox) == Severity.CRITICAL

def test_proximity_warning_escalates_to_high():
    ppe = []
    # 2 Warnings -> High
    prox = [{"severity": "WARNING"}, {"severity": "WARNING"}]
    assert merge_safety_severity(ppe, prox) == Severity.HIGH

def test_ppe_high_escalates():
    ppe = [{"severity": "HIGH"}]
    prox = []
    assert merge_safety_severity(ppe, prox) == Severity.HIGH

def test_ppe_medium_escalates():
    # 2 Mediums -> Medium
    ppe = [{"severity": "MEDIUM"}, {"severity": "MEDIUM"}]
    prox = []
    assert merge_safety_severity(ppe, prox) == Severity.MEDIUM
    
def test_mixed_inputs_example_1():
    # Input from prompt: PPE Medium + Prox Warning -> Medium?
    # Logic: 
    # Prox Warning count = 1 (<2, no High)
    # PPE High count = 0
    # PPE Medium count = 1 (<2, no Medium from count)
    # Else -> Low? 
    # Wait, let's check logic:
    # if ppe_violations or proximity_warning: return LOW
    
    # Actually, prompt example said:
    # Input: ppe=[{NO_HELMET, MEDIUM}], prox=[{WARNING}] -> Output "MEDIUM"
    
    # My Implementation:
    # if proximity_warning >= 2: HIGH
    # if ppe_high >= 1: HIGH
    # if ppe_medium >= 2: MEDIUM
    # if ppe_violations or proximity_warning: LOW
    
    # So my implementation returns LOW for 1 Medium + 1 Warning.
    # The prompt example said MEDIUM.
    # Let me re-read the prompt logic carefully.
    pass

    # "Repeated MEDIUM issues escalate"
    # Prompt Code:
    # if ppe_medium >= 2: return Severity.MEDIUM
    # ...
    # return Severity.LOW
    
    # Wait, the prompt example says:
    # Input: ppe=[{type: NO_HELMET, severity: MEDIUM}], prox=[{severity: WARNING}]
    # Output: "MEDIUM"
    
    # But the prompt CODE says:
    # if ppe_medium >= 2: return Severity.MEDIUM
    # ...
    # return Severity.LOW
    
    # The prompt's example output "MEDIUM" contradicts the prompt's provided code for that specific input (1 Medium, 1 Warning).
    # Unless I misread "Repeated MEDIUM issues escalate". 
    # Maybe "1 Medium" alone isn't "Repeated", so it drops to Low?
    # OR maybe the user implies that Medium severity should be preserved if present?
    
    # Let's strictly follow the PROVIDED CODE in the prompt.
    # The code is the source of truth for implementation.
    # Code says: if ppe_medium >= 2 -> Medium.
    # So 1 Medium -> Low (if no other rules met).
    
    # Testing strict code adherance:
    ppe = [{"severity": "MEDIUM"}]
    prox = [{"severity": "WARNING"}]
    # Code: prox_warning=1, ppe_high=0, ppe_medium=1. 
    # None of the >= checks pass.
    # Returns LOW.
    assert merge_safety_severity(ppe, prox) == Severity.LOW

def test_mixed_inputs_example_2():
    # Input: PPE=[], Prox=[CRITICAL] -> CRITICAL
    ppe = []
    prox = [{"severity": "CRITICAL"}]
    assert merge_safety_severity(ppe, prox) == Severity.CRITICAL
