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
            
            exifdata = image.getexif()
            
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    
                    if tag_name == 'GPSInfo':
                        gps_data = {}
                        for gps_tag_id in value:
                            gps_tag_name = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                            gps_value = value[gps_tag_id]
                            gps_data[gps_tag_name] = str(gps_value)
                        metadata['GPSInfo'] = str(gps_data)
                    else:
                        try:
                            metadata[str(tag_name)] = str(value)[:500]
                        except:
                            metadata[str(tag_name)] = str(type(value))
            
            file_obj.seek(0)
            tags = exifread.process_file(file_obj, details=False)
            
            for tag, value in tags.items():
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    tag_str = str(tag)
                    if tag_str not in metadata:
                        try:
                            metadata[tag_str] = str(value)[:500]
                        except:
                            pass
            
            if hasattr(image, 'info') and image.info:
                for key, value in image.info.items():
                    if key not in ['exif', 'icc_profile']:
                        try:
                            if isinstance(value, (str, int, float)):
                                metadata[f'PNG_{key}'] = str(value)[:500]
                        except:
                            pass
            
        except Exception as e:
            print(f"Error extracting image metadata: {str(e)}")
        
        return metadata
    
    @staticmethod
    def extract_metadata(file_obj, file_type):
        try:
            if file_type.startswith('image/'):
                return MetadataExtractor.extract_from_image(file_obj)
        except Exception as e:
            print(f"Error in extract_metadata: {str(e)}")
        
        return {}
    
    @staticmethod
    def categorize_metadata(key, value):
        key_lower = key.lower()
        
        location_keywords = ['gps', 'latitude', 'longitude', 'location', 'coordinates']
        device_keywords = ['make', 'model', 'device', 'camera', 'lens']
        personal_keywords = ['author', 'artist', 'creator', 'owner', 'copyright']
        temporal_keywords = ['datetime', 'date', 'time', 'timestamp']
        camera_keywords = ['exposure', 'iso', 'flash', 'focal', 'aperture', 'shutter']
        software_keywords = ['software', 'program', 'application', 'editor']
        
        if any(keyword in key_lower for keyword in location_keywords):
            return 'location'
        elif any(keyword in key_lower for keyword in device_keywords):
            return 'device'
        elif any(keyword in key_lower for keyword in personal_keywords):
            return 'personal'
        elif any(keyword in key_lower for keyword in temporal_keywords):
            return 'temporal'
        elif any(keyword in key_lower for keyword in camera_keywords):
            return 'camera'
        elif any(keyword in key_lower for keyword in software_keywords):
            return 'software'
        
        return 'other'