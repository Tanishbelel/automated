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
    # Define realistic device pool for "Plausible Deniability"
    device_pool = [
        {"Camera": "Sony ILCE-7M4", "Software": "Sony Imaging Edge"},
        {"Camera": "iPhone 13 Pro", "Software": "iOS 15.4"},
        {"Camera": "Canon EOS 5D Mark IV", "Software": "Digital Photo Professional"},
        {"Camera": "Nikon D850", "Software": "Nikon Capture NX-D"},
        {"Camera": "Microsoft Word 2019", "Software": "Microsoft Office 365"}
    ]
    
    selected_device = random.choice(device_pool)
    
    shift_days = random.choice([-3, -2, -1, 1, 2, 3])
    synthetic_time = datetime.now() + timedelta(days=shift_days)
    synthetic_time_str = synthetic_time.strftime("%Y:%m:%d %H:%M:%S")

    replaced = {
        "Camera": selected_device["Camera"],
        "Software": selected_device["Software"],
        "Timestamp": synthetic_time_str
    }
    
    # GPS is removed entirely for all profiles
    stripped = ["GPS", "Author", "DeviceSerial"]
    
    platform_lower = platform.lower()
    
    if platform_lower == "instagram":
        stripped.extend(["OriginalTimestamp", "UserComment", "ImageDescription"])
    elif platform_lower == "linkedin":
        stripped.extend(["OriginalTimestamp", "UserComment"])
    elif platform_lower == "twitter":
        stripped.extend(["OriginalTimestamp"])
    elif platform_lower == "whatsapp":
        stripped.extend(["OriginalTimestamp", "ImageDescription", "UserComment"])
    else:
        stripped.extend(["OriginalTimestamp", "UserComment", "ImageDescription"])
        
    return {
        "stripped": stripped,
        "replaced": replaced
    }
