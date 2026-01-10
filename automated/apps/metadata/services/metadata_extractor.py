# apps/metadata/services/metadata_extractor.py
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import mimetypes
from datetime import datetime

class MetadataExtractor:
    """Extracts metadata from various file formats"""
    
    def __init__(self, file_obj, file_name):
        self.file_obj = file_obj
        self.file_name = file_name
        self.mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
    
    def extract(self):
        """Main extraction method"""
        if self.mime_type.startswith('image/'):
            return self.extract_image_metadata()
        elif self.mime_type == 'application/pdf':
            return self.extract_pdf_metadata()
        elif self.mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return self.extract_docx_metadata()
        else:
            return self.extract_basic_metadata()
    
    def extract_image_metadata(self):
        """Extract metadata from image files"""
        metadata = {
            'file_info': self._get_file_info(),
            'exif': {},
            'gps': {},
            'camera': {},
            'software': {},
            'author': {},
            'datetime': {},
        }
        
        try:
            # Reset file pointer
            self.file_obj.seek(0)
            
            # Using PIL
            image = Image.open(self.file_obj)
            exif_data = image._getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata['exif'][tag] = str(value)
                    
                    # Categorize metadata
                    if tag in ['Make', 'Model', 'LensMake', 'LensModel']:
                        metadata['camera'][tag] = str(value)
                    elif tag in ['Software', 'ProcessingSoftware']:
                        metadata['software'][tag] = str(value)
                    elif tag in ['Artist', 'Copyright', 'Author']:
                        metadata['author'][tag] = str(value)
                    elif tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        metadata['datetime'][tag] = str(value)
                    elif tag == 'GPSInfo':
                        metadata['gps'] = self._extract_gps_info(value)
            
            # Image dimensions
            metadata['file_info']['width'] = image.width
            metadata['file_info']['height'] = image.height
            metadata['file_info']['format'] = image.format
            metadata['file_info']['mode'] = image.mode
            
        except Exception as e:
            metadata['error'] = str(e)
        
        # Use exifread as fallback
        try:
            self.file_obj.seek(0)
            tags = exifread.process_file(self.file_obj, details=False)
            
            for tag, value in tags.items():
                if tag not in metadata['exif']:
                    metadata['exif'][tag] = str(value)
        except Exception:
            pass
        
        return metadata
    
    def _extract_gps_info(self, gps_data):
        """Extract GPS information"""
        gps_info = {}
        
        for key, value in gps_data.items():
            tag = GPSTAGS.get(key, key)
            gps_info[tag] = str(value)
        
        # Calculate decimal coordinates if possible
        try:
            if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = self._convert_to_degrees(gps_data[2])
                lon = self._convert_to_degrees(gps_data[4])
                
                if gps_data.get(1) == 'S':
                    lat = -lat
                if gps_data.get(3) == 'W':
                    lon = -lon
                
                gps_info['latitude'] = lat
                gps_info['longitude'] = lon
        except Exception:
            pass
        
        return gps_info
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees"""
        d, m, s = value
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
    
    def extract_pdf_metadata(self):
        """Extract metadata from PDF files"""
        metadata = {
            'file_info': self._get_file_info(),
            'pdf_info': {},
            'author': {},
            'software': {},
            'datetime': {},
        }
        
        try:
            import PyPDF2
            
            self.file_obj.seek(0)
            pdf_reader = PyPDF2.PdfReader(self.file_obj)
            
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    clean_key = key.replace('/', '')
                    metadata['pdf_info'][clean_key] = str(value)
                    
                    if clean_key in ['Author', 'Creator']:
                        metadata['author'][clean_key] = str(value)
                    elif clean_key in ['Producer', 'Creator']:
                        metadata['software'][clean_key] = str(value)
                    elif clean_key in ['CreationDate', 'ModDate']:
                        metadata['datetime'][clean_key] = str(value)
            
            metadata['file_info']['pages'] = len(pdf_reader.pages)
            
        except ImportError:
            metadata['error'] = 'PyPDF2 not installed'
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def extract_docx_metadata(self):
        """Extract metadata from DOCX files"""
        metadata = {
            'file_info': self._get_file_info(),
            'core_properties': {},
            'author': {},
            'software': {},
            'datetime': {},
        }
        
        try:
            from docx import Document
            
            self.file_obj.seek(0)
            doc = Document(self.file_obj)
            core_props = doc.core_properties
            
            props = {
                'author': core_props.author,
                'created': core_props.created,
                'modified': core_props.modified,
                'last_modified_by': core_props.last_modified_by,
                'revision': core_props.revision,
                'title': core_props.title,
                'subject': core_props.subject,
            }
            
            for key, value in props.items():
                if value:
                    metadata['core_properties'][key] = str(value)
                    
                    if key in ['author', 'last_modified_by']:
                        metadata['author'][key] = str(value)
                    elif key in ['created', 'modified']:
                        metadata['datetime'][key] = str(value)
            
        except ImportError:
            metadata['error'] = 'python-docx not installed'
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def extract_basic_metadata(self):
        """Extract basic file information"""
        return {
            'file_info': self._get_file_info(),
        }
    
    def _get_file_info(self):
        """Get basic file information"""
        self.file_obj.seek(0, 2)  # Seek to end
        file_size = self.file_obj.tell()
        self.file_obj.seek(0)  # Reset
        
        return {
            'name': self.file_name,
            'size': file_size,
            'mime_type': self.mime_type,
        }