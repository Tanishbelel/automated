def score_risk(metadata_fields: list[str], pii_results: list[dict]) -> int:
    """
    Calculates a privacy risk score (0-100) based on remaining metadata and PII.
    
    Weighting:
    GPS coordinates present: +35 points
    Author / username present: +25 points
    Device serial / IMEI present: +20 points
    Camera make/model present: +10 points
    Software + version present: +7 points
    Timestamps present: +5 points
    PII patterns found (per pattern): +10 points each, capped at +30
    Cap total at 100. Return 0 if nothing is found.
    """
    score = 0
    
    # Analyze metadata fields
    # Make sure matching is case insensitive and handles different variations
    metadata_lower = [f.lower() for f in metadata_fields]
    
    # GPS check
    if any(any(kw in f for kw in ["gps", "latitude", "longitude"]) for f in metadata_lower):
        score += 35
        
    # Author/username check
    if any(any(kw in f for kw in ["author", "user", "creator", "owner"]) for f in metadata_lower):
        score += 25
        
    # Device serial / IMEI check
    if any(any(kw in f for kw in ["serial", "imei", "device id"]) for f in metadata_lower):
        score += 20
        
    # Camera make/model check
    if any(any(kw in f for kw in ["make", "model", "camera"]) for f in metadata_lower):
        score += 10
        
    # Software + version check
    if any(any(kw in f for kw in ["software", "version", "program"]) for f in metadata_lower):
        score += 7
        
    # Timestamps check
    if any(any(kw in f for kw in ["time", "date"]) for f in metadata_lower):
        score += 5

    # Analyze PII results
    pii_count = len(pii_results)
    pii_score = min(pii_count * 10, 30)
    score += pii_score
    
    # Cap total at 100
    return min(score, 100)
