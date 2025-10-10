# flask-backend/utils/rule_validator.py

def apply_severity_correction(text, ml_severity_label):
    """
    Applies rule-based correction to the ML model's severity prediction 
    based on the presence of high-impact keywords. This is used to override
    incorrect predictions (like "Low" for a massive earthquake) for demonstration quality.
    
    Args:
        text (str): The input text (e.g., news headline).
        ml_severity_label (str): The severity predicted by the ML model ('Low', 'Medium', 'High').
        
    Returns:
        str: The corrected severity label.
    """
    
    # Standardize text for case-insensitive keyword checking
    clean_text = text.lower()
    
    # --- Rule 1: High Severity Keywords ---
    # These words almost guarantee a High severity event
    high_keywords = [
        "massive", "strong", "severe", "widespread", "fatalities", 
        "collapsed", "emergency", "evacuation", "major damage", "submerged",
        "catastrophic", "destroyed", "rescue needed", "people trapped", "major loss"
    ]
    
    # --- Rule 2: Medium Severity Keywords ---
    # These words imply significant impact, but not catastrophic
    medium_keywords = [
        "minor damage", "disruption", "traffic jam", "many injured", 
        "large area", "significant", "alert issued", "several buildings", "minor injuries"
    ]

    # --- Apply Correction Logic ---
    
    # If the ML model predicted Low/Medium, check if a High keyword is present.
    if ml_severity_label in ['Low', 'Medium']:
        if any(keyword in clean_text for keyword in high_keywords):
            # Override to High if the text contains high-impact terms
            return "High"
    
    # If the ML model predicted Low, check if a Medium keyword is present.
    if ml_severity_label == 'Low':
        if any(keyword in clean_text for keyword in medium_keywords):
            # Override to Medium if the text contains moderate-impact terms
            return "Medium"
    
    # If no rule triggered an override, return the original ML prediction
    return ml_severity_label