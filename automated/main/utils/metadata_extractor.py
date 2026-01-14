from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


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
                            gps_data[gps_tag_name] = str(value[gps_tag_id])
                        metadata['GPSInfo'] = str(gps_data)
                    else:
                        metadata[str(tag_name)] = str(value)[:500]
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        return metadata
    
    @staticmethod
    def extract_metadata(file_obj, file_type):
        if file_type.startswith('image/'):
            return MetadataExtractor.extract_from_image(file_obj)
        return {}
    
    @staticmethod
    def categorize_metadata(key, value):
        key_lower = key.lower()
        
        if any(k in key_lower for k in ['gps', 'latitude', 'longitude', 'location']):
            return 'location'
        elif any(k in key_lower for k in ['make', 'model', 'device', 'camera']):
            return 'device'
        elif any(k in key_lower for k in ['author', 'artist', 'creator', 'copyright']):
            return 'personal'
        elif any(k in key_lower for k in ['datetime', 'date', 'time']):
            return 'temporal'
        elif any(k in key_lower for k in ['exposure', 'iso', 'flash', 'focal']):
            return 'camera'
        elif any(k in key_lower for k in ['software', 'program', 'application']):
            return 'software'
        
        return 'other'