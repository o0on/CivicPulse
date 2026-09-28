import pytest
from pydantic import ValidationError
from app.models import Category, Priority
from app.providers.triage.base import TriageResult
from app.providers.triage.rule_based import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

def test_rules_water_keywords():
    triage = RuleBasedTriage()
    result = triage.triage("The water pipe is leaking heavily on my street.")
    assert result.category == Category.water

def test_rules_electricity_keywords():
    triage = RuleBasedTriage()
    result = triage.triage("There has been no power for 5 hours due to load shedding.")
    assert result.category == Category.electricity

def test_rules_high_priority_emergency():
    triage = RuleBasedTriage()
    result = triage.triage("A massive water burst is causing flooding everywhere.")
    assert result.priority == Priority.high

def test_rules_always_succeeds():
    triage = RuleBasedTriage()
    result = triage.triage("xyz123 gibberish data that means nothing")
    assert isinstance(result, TriageResult)

def test_rules_fallback_category():
    triage = RuleBasedTriage()
    result = triage.triage("I need someone to look at this issue.")
    assert result.category == Category.other

def test_simulated_deterministic():
    triage = SimulatedTriage()
    text = "The road is completely broken outside my house."
    result1 = triage.triage(text)
    result2 = triage.triage(text)
    assert result1.category == result2.category
    assert result1.priority == result2.priority
    assert result1.summary == result2.summary
    assert result1.confidence == result2.confidence

def test_simulated_error_injection():
    triage = SimulatedTriage(inject_error=True)
    with pytest.raises(RuntimeError):
        triage.triage("This should fail")

def test_simulated_summary_length():
    triage = SimulatedTriage()
    long_text = "There is a massive pothole. " * 50
    result = triage.triage(long_text)
    assert len(result.summary) <= 140

def test_triage_result_validation():
    with pytest.raises(ValidationError):
        TriageResult(
            category=Category.water,
            priority=Priority.normal,
            summary="Valid summary",
            confidence=1.5 # Invalid confidence
        )

def test_triage_result_summary_max_length():
    with pytest.raises(ValidationError):
        TriageResult(
            category=Category.other,
            priority=Priority.low,
            summary="A" * 141, # Over 140 chars
            confidence=0.9
        )
