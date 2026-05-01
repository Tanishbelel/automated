from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PipelineResult(BaseModel):
    original_filename: str
    risk_score: int
    fields_removed: List[str]
    pii_patterns_found: List[Dict[str, Any]]
    platform_profile_applied: str
    output_file_path: str
    processing_timestamp: datetime
    sha256_hash: str

class MalwareScanResult(BaseModel):
    status: str  # "clean", "infected", "error"
    threat_name: Optional[str] = None

class MetadataStripResult(BaseModel):
    fields_removed: List[str]
    file_path: str

class PIIRedactResult(BaseModel):
    patterns_found: List[Dict[str, Any]]
    file_path: str
