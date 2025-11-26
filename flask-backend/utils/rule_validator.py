# flask-backend/utils/rule_validator.py

def apply_severity_correction(text, ml_severity_label):
    """
    Applies rule-based correction to the ML model's severity prediction.
    Prioritizes keyword detection to ensure High, Medium, and Low are 
    correctly classified even if the ML model is biased.
    
    Hierarchy of checks:
    1. High Keywords -> Returns "High"
    2. Medium Keywords -> Returns "Medium"
    3. Low Keywords -> Returns "Low"
    4. Fallback -> Returns original ML prediction
    """
    
    # Standardize text for case-insensitive keyword checking
    clean_text = text.lower()
    
    # --- Rule 1: High Severity Keywords ---
    # Critical events, loss of life, major destruction
    high_keywords = [
        "massive", "strong", "severe", "widespread", "fatalities", "death", "dead",
        "collapsed", "emergency", "evacuation", "major damage", "submerged",
        "catastrophic", "destroyed", "rescue needed", "people trapped", "major loss",
        "major", "critical", "intense", "urgent", "extreme"
    ]
    
    # --- Rule 2: Medium Severity Keywords ---
    # Significant impact, injuries, infrastructure damage, but not total devastation
    medium_keywords = [
        "moderate", "partial", "significant", "injured", "hospitalized",
        "stranded", "affected", "disruption", "traffic jam", "blocked",
        "power outage", "damaged", "relief", "alert", "warning", "rising water",
        "heavy rain", "waterlogging"
    ]

    # --- Rule 3: Low Severity Keywords ---
    # Minor events, drills, false alarms, minimal impact
    low_keywords = [
        "minor", "small", "light", "no damage", "no casualties", "no injury",
        "safe", "controlled", "drill", "test", "false alarm", "rumor",
        "subsiding", "normal", "minimal", "negligible", "tremor"
    ]

    # --- Apply Correction Logic (Strict Hierarchy) ---
    
    # 1. Check High
    if any(keyword in clean_text for keyword in high_keywords):
        return "High"
        
    # 2. Check Medium
    if any(keyword in clean_text for keyword in medium_keywords):
        return "Medium"
        
    # 3. Check Low
    if any(keyword in clean_text for keyword in low_keywords):
        return "Low"
    
    # 4. If no keywords match, trust the ML model
    return ml_severity_label