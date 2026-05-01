import piexif
import fitz  # PyMuPDF
import mimetypes
import shutil
import os

def inject_signature(filepath: str, replacements: dict) -> str:
    """
    Writes synthetic metadata values from the platform profile into the file's metadata.
    Uses piexif for images and PyMuPDF (fitz) for PDFs.
    Returns the modified file path.
    """
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        return filepath
        
    try:
        if mime_type.startswith('image/'):
            _inject_image_metadata(filepath, replacements)
        elif mime_type == 'application/pdf':
            _inject_pdf_metadata(filepath, replacements)
    except Exception as e:
        print(f"Failed to inject signature for {filepath}: {e}")
        
    return filepath

def _inject_image_metadata(filepath: str, replacements: dict):
    try:
        exif_dict = piexif.load(filepath)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    
    # Make mapping of custom replacements to piexif tags
    if "Camera" in replacements:
        exif_dict["0th"][piexif.ImageIFD.Make] = b"Canon"
        exif_dict["0th"][piexif.ImageIFD.Model] = replacements["Camera"].encode()
    if "Software" in replacements:
        exif_dict["0th"][piexif.ImageIFD.Software] = replacements["Software"].encode()
    if "Timestamp" in replacements:
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = replacements["Timestamp"].encode()
        exif_dict["0th"][piexif.ImageIFD.DateTime] = replacements["Timestamp"].encode()
        
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)

def _inject_pdf_metadata(filepath: str, replacements: dict):
    doc = fitz.open(filepath)
    metadata = doc.metadata or {}
    
    if "Software" in replacements:
        metadata["creator"] = replacements["Software"]
        metadata["producer"] = replacements["Software"]
        
    if "Timestamp" in replacements:
        # PDF expects format like D:YYYYMMDDHHmmSSZ
        ts_str = replacements["Timestamp"].replace(":", "").replace(" ", "")
        metadata["creationDate"] = f"D:{ts_str}Z"
        metadata["modDate"] = f"D:{ts_str}Z"
        
    if "Camera" in replacements:
        metadata["subject"] = replacements["Camera"] # Abuse subject for Camera
        
    doc.set_metadata(metadata)
    
    # Save to a temporary file then replace
    temp_path = filepath + ".tmp.pdf"
    doc.save(temp_path)
    doc.close()
    
    shutil.move(temp_path, filepath)
