from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import json

class MetadataExtractor:
    
    # Sensitive metadata categories
    LOCATION_KEYS = [
        'GPSInfo', 'GPS', 'GPSLatitude', 'GPSLongitude', 'GPSAltitude',
        'GPSTimeStamp', 'GPSDateStamp', 'GPSProcessingMethod', 'GPSDestination',
        'Location', 'LocationCreated', 'LocationShown'
    ]
    
    PERSONAL_KEYS = [
        'Copyright', 'CopyrightNotice', 'Owner', 'OwnerName', 'Rights',
        'PersonInImage', 'Subject', 'Name', 'Email', 'Phone', 'Address'
    ]
    
    AUTHOR_KEYS = [
        'Author', 'Artist', 'Creator', 'By-line', 'Credit', 'Contributors',
        'Writer', 'Photographer', 'CaptionWriter', 'dc:creator'
    ]
    
    DEVICE_KEYS = [
        'Make', 'Model', 'DeviceName', 'HostComputer', 'LensMake',
        'LensModel', 'Scanner', 'DeviceManufacturer', 'DeviceModel',
        'UniqueCameraModel', 'LocalizedCameraModel', 'CameraSerialNumber',
        'LensSerialNumber', 'InternalSerialNumber'
    ]
    
    CAMERA_KEYS = [
        'ExifImageWidth', 'ExifImageHeight', 'FocalLength', 'FNumber',
        'ISO', 'ISOSpeedRatings', 'ExposureTime', 'ShutterSpeedValue',
        'ApertureValue', 'Flash', 'WhiteBalance', 'FocalLengthIn35mmFilm'
    ]
    
    SOFTWARE_KEYS = [
        'Software', 'ProcessingSoftware', 'CreatorTool', 'Producer',
        'Application', 'Program', 'ProcessingTool', 'xmp:CreatorTool'
    ]
    
    TIMESTAMP_KEYS = [
        'DateTime', 'DateTimeOriginal', 'DateTimeDigitized', 'CreateDate',
        'ModifyDate', 'MetadataDate', 'CreationDate', 'ModDate',
        'xmp:CreateDate', 'xmp:ModifyDate'
    ]
    
    @staticmethod
    def extract_metadata(file, file_type):
        """
        Extract metadata based on file type
        """
        try:
            if file_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
                           'image/webp', 'image/tiff', 'image/bmp']:
                return MetadataExtractor.extract_image_metadata(file)
            
            elif file_type == 'application/pdf':
                return MetadataExtractor.extract_pdf_metadata(file)
            
            else:
                return {}
        
        except Exception as e:
            print(f"Metadata extraction error: {str(e)}")
            return {}
    
    @staticmethod
    def extract_image_metadata(file):
        """
        Extract EXIF and other metadata from images
        """
        metadata = {}
        
        try:
            if hasattr(file, 'seek'):
                file.seek(0)
            
            image = Image.open(file)
            
            # Extract basic info
            metadata['Format'] = image.format
            metadata['Size'] = f"{image.size[0]}x{image.size[1]}"
            metadata['Mode'] = image.mode
            
            # Extract EXIF data
            exif_data = image._getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # Handle GPS Info separately
                    if tag == 'GPSInfo':
                        gps_data = {}
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = str(gps_value)
                        metadata['GPSInfo'] = json.dumps(gps_data)
                    
                    # Handle MakerNote and UserComment (binary data)
                    elif tag in ['MakerNote', 'UserComment']:
                        if isinstance(value, bytes):
                            try:
                                metadata[tag] = value.decode('utf-8', errors='ignore')[:100]
                            except:
                                metadata[tag] = f"<Binary data, {len(value)} bytes>"
                        else:
                            metadata[tag] = str(value)[:100]
                    
                    # Convert other values to string
                    else:
                        try:
                            if isinstance(value, bytes):
                                metadata[tag] = value.decode('utf-8', errors='ignore')[:500]
                            elif isinstance(value, (tuple, list)):
                                metadata[tag] = str(value)
                            else:
                                metadata[tag] = str(value)
                        except:
                            metadata[tag] = f"<Unparseable: {type(value).__name__}>"
            
        except Exception as e:
            print(f"Image metadata extraction error: {str(e)}")
        
        return metadata
    
    @staticmethod
    def extract_pdf_metadata(file):
        """
        Extract metadata from PDF files using multiple methods
        """
        metadata = {}
        
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                
                if hasattr(file, 'seek'):
                    file.seek(0)
                
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract document info
                if pdf_reader.metadata:
                    for key, value in pdf_reader.metadata.items():
                        # Remove the '/' prefix from keys
                        clean_key = key.lstrip('/')
                        if value:
                            metadata[clean_key] = str(value)
                
                # Add page count
                metadata['PageCount'] = str(len(pdf_reader.pages))
                
                # Try to get XMP metadata
                if hasattr(pdf_reader, 'xmp_metadata') and pdf_reader.xmp_metadata:
                    xmp = pdf_reader.xmp_metadata
                    
                    # Extract common XMP fields
                    xmp_fields = [
                        'dc_title', 'dc_creator', 'dc_subject', 'dc_description',
                        'dc_publisher', 'dc_contributor', 'dc_date', 'dc_type',
                        'dc_format', 'dc_identifier', 'dc_language', 'dc_rights',
                        'pdf_keywords', 'pdf_producer', 'xmp_create_date',
                        'xmp_modify_date', 'xmp_metadata_date', 'xmp_creator_tool'
                    ]
                    
                    for field in xmp_fields:
                        try:
                            value = getattr(xmp, field, None)
                            if value:
                                clean_key = field.replace('_', ':').title()
                                metadata[clean_key] = str(value)
                        except:
                            pass
                
                return metadata
            
            except ImportError:
                print("PyPDF2 not installed, trying alternative methods")
        
        except Exception as e:
            print(f"PyPDF2 extraction error: {str(e)}")
        
        # Try pikepdf as backup
        try:
            import pikepdf
            
            if hasattr(file, 'seek'):
                file.seek(0)
            
            with pikepdf.open(file) as pdf:
                # Extract document info
                if pdf.docinfo:
                    for key, value in pdf.docinfo.items():
                        clean_key = key.lstrip('/')
                        metadata[clean_key] = str(value)
                
                # Extract XMP metadata
                if pdf.open_metadata():
                    xmp = pdf.open_metadata()
                    
                    # Common XMP namespaces
                    namespaces = {
                        'dc': 'http://purl.org/dc/elements/1.1/',
                        'xmp': 'http://ns.adobe.com/xap/1.0/',
                        'pdf': 'http://ns.adobe.com/pdf/1.3/',
                        'pdfx': 'http://ns.adobe.com/pdfx/1.3/',
                        'photoshop': 'http://ns.adobe.com/photoshop/1.0/'
                    }
                    
                    for prefix, uri in namespaces.items():
                        try:
                            for key in xmp:
                                if uri in str(key):
                                    value = xmp[key]
                                    if value:
                                        metadata[f"{prefix}:{key.split('}')[-1]}"] = str(value)
                        except:
                            pass
                
                metadata['PageCount'] = str(len(pdf.pages))
            
            return metadata
        
        except ImportError:
            print("pikepdf not installed")
        except Exception as e:
            print(f"pikepdf extraction error: {str(e)}")
        
        # Try PyMuPDF (fitz) as last resort
        try:
            import fitz  # PyMuPDF
            
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Read file into memory
            file_data = file.read()
            pdf_document = fitz.open(stream=file_data, filetype="pdf")
            
            # Extract metadata
            pdf_metadata = pdf_document.metadata
            if pdf_metadata:
                for key, value in pdf_metadata.items():
                    if value:
                        metadata[key] = str(value)
            
            metadata['PageCount'] = str(pdf_document.page_count)
            pdf_document.close()
            
            return metadata
        
        except ImportError:
            print("PyMuPDF not installed")
        except Exception as e:
            print(f"PyMuPDF extraction error: {str(e)}")
        
        return metadata
    
    @staticmethod
    def categorize_metadata(key, value):
        """
        Categorize metadata by sensitivity type
        """
        key_upper = key.upper()
        
        # Check each category
        if any(loc_key.upper() in key_upper for loc_key in MetadataExtractor.LOCATION_KEYS):
            return 'location'
        
        if any(pers_key.upper() in key_upper for pers_key in MetadataExtractor.PERSONAL_KEYS):
            return 'personal'
        
        if any(auth_key.upper() in key_upper for auth_key in MetadataExtractor.AUTHOR_KEYS):
            return 'author'
        
        if any(dev_key.upper() in key_upper for dev_key in MetadataExtractor.DEVICE_KEYS):
            return 'device'
        
        if any(cam_key.upper() in key_upper for cam_key in MetadataExtractor.CAMERA_KEYS):
            return 'camera'
        
        if any(soft_key.upper() in key_upper for soft_key in MetadataExtractor.SOFTWARE_KEYS):
            return 'software'
        
        if any(time_key.upper() in key_upper for time_key in MetadataExtractor.TIMESTAMP_KEYS):
            return 'timestamp'
        
        return 'other'