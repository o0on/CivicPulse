from app.models import Category, Priority
from app.providers.triage.base import TriageResult


class RuleBasedTriage:
    name: str = "rules"

    async def triage(self, text: str, location: str = "") -> TriageResult:
        text_lower = text.lower()
        
        # Determine Category
        category = Category.other
        if any(kw in text_lower for kw in ["water", "pani", "nullah", "drain", "sewerage", "sewage"]):
            if any(kw in text_lower for kw in ["nullah", "sewerage", "sewage"]):
                category = Category.sanitation
            else:
                category = Category.water
        elif any(kw in text_lower for kw in ["electricity", "bijli", "transformer", "load-shedding", "load shedding", "power", "bijli ka khamba"]):
            if "bijli ka khamba" in text_lower:
                category = Category.streetlights
            else:
                category = Category.electricity
        elif any(kw in text_lower for kw in ["road", "sadak", "pothole"]):
            category = Category.roads
        elif any(kw in text_lower for kw in ["light", "street light"]):
            category = Category.streetlights
        elif any(kw in text_lower for kw in ["garbage", "kachra", "waste"]):
            category = Category.sanitation

        # Determine Priority
        priority = Priority.normal
        if any(kw in text_lower for kw in ["flooding", "burst", "emergency", "urgent"]):
            priority = Priority.high
        elif any(kw in text_lower for kw in ["dim", "slow", "occasional"]):
            priority = Priority.low
        elif any(kw in text_lower for kw in ["broken", "damaged"]):
            priority = Priority.normal
            
        return TriageResult(
            category=category,
            priority=priority,
            summary=text[:137] + "..." if len(text) > 140 else text,
            confidence=0.7 if category != Category.other else 0.4
        )
