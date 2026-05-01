import random
from datetime import datetime, timedelta

def apply_platform_profile(filepath: str, platform: str) -> dict:
    """
    Applies a platform-specific profile to determine which metadata is stripped
    and which is replaced with synthetic values.
    
    platform: "instagram", "linkedin", "twitter", "whatsapp", "general"
    
    Returns a dict:
    {
        "stripped": list[str],
        "replaced": dict
    }
    """
    # Define synthetic values
    # Shift timestamp by random +/- 1-3 days
    shift_days = random.choice([-3, -2, -1, 1, 2, 3])
    synthetic_time = datetime.now() + timedelta(days=shift_days)
    synthetic_time_str = synthetic_time.strftime("%Y:%m:%d %H:%M:%S")

    replaced = {
        "Camera": "Canon EOS R50",
        "Software": "Adobe Lightroom 6.0",
        "Timestamp": synthetic_time_str
    }
    
    stripped = ["GPS", "Author", "DeviceSerial", "OriginalTimestamp", "UserComment"]

    # Different platforms might have varying rules, but for the scope of this assignment, 
    # we return standard synthetic data and completely remove GPS for all.
    # We can customize this logic based on `platform` if needed later.
    
    if platform.lower() == "instagram":
        stripped.append("ImageDescription")
    elif platform.lower() == "linkedin":
        # Maybe retain some basic professional software metadata
        pass
    
    return {
        "stripped": stripped,
        "replaced": replaced
    }
