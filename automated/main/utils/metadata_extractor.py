import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io

class MetadataExtractor:
    
    @staticmethod
    def extract_from_image(file_obj):
        metadata = {}
        
        try:
            file_obj.seek(0)
            image = Image.open(file_obj)
            
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif_data = image._getexif()
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    
                    if tag_name == 'GPSInfo':
                        gps_data = {}
                        for gps_tag_id, gps_value in value.items():
                            gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag_name] = str(gps_value)
                        metadata['GPSInfo'] = str(gps_data)
                    else:
                        metadata[str(tag_name)] = str(value)
            
            file_obj.seek(0)
            tags = exifread.process_file(file_obj, details=False)
            
            for tag, value in tags.items():
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    tag_str = str(tag)
                    if tag_str not in metadata:
                        metadata[tag_str] = str(value)
            
            if image.info:
                for key, value in image.info.items():
                    if key not in ['exif', 'icc_profile'] and isinstance(value, (str, int, float)):
                        metadata[f'PNG_{key}'] = str(value)
            
        except Exception as e:
            pass
        
        return metadata
    
    @staticmethod
    def extract_metadata(file_obj, file_type):
        if file_type.startswith('image/'):
            return MetadataExtractor.extract_from_image(file_obj)
        
        return {}
    
    @staticmethod
    def categorize_metadata(key, value):
        key_lower = key.lower()
        
        location_keywords = ['gps', 'latitude', 'longitude', 'location', 'coordinates']
        device_keywords = ['make', 'model', 'device', 'camera', 'lens']
        author_keywords = ['author', 'artist', 'creator', 'owner', 'copyright']
        timestamp_keywords = ['datetime', 'date', 'time', 'timestamp']
        camera_keywords = ['exposure', 'iso', 'flash', 'focal', 'aperture', 'shutter']
        software_keywords = ['software', 'program', 'application', 'editor']
        
        if any(keyword in key_lower for keyword in location_keywords):
            return 'location'
        elif any(keyword in key_lower for keyword in device_keywords):
            return 'device'
        elif any(keyword in key_lower for keyword in author_keywords):
            return 'author'
        elif any(keyword in key_lower for keyword in timestamp_keywords):
            return 'timestamp'
        elif any(keyword in key_lower for keyword in camera_keywords):
            return 'camera'
        elif any(keyword in key_lower for keyword in software_keywords):
            return 'software'
        
        return 'other'