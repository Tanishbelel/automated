# apps/metadata/services/metadata_remover.py
from PIL import Image
import io
import mimetypes

class MetadataRemover:
    """Removes metadata from various file formats"""
    
    def __init__(self, file_obj, file_name, platform=None):
        self.file_obj = file_obj
        self.file_name = file_name
        self.mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        self.platform = platform
    
    def remove(self):
        """Main removal method"""
        if self.mime_type.startswith('image/'):
            return self.remove_image_metadata()
        elif self.mime_type == 'application/pdf':
            return self.remove_pdf_metadata()
        elif self.mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return self.remove_docx_metadata()
        else:
            # For unsupported formats, return original file
            self.file_obj.seek(0)
            return self.file_obj.read(), self.mime_type
    
    def remove_image_metadata(self):
        """Remove metadata from image files"""
        try:
            self.file_obj.seek(0)
            image = Image.open(self.file_obj)
            
            # Get the format
            image_format = image.format or 'JPEG'
            
            # Create a new image without EXIF data
            # Convert RGBA to RGB if saving as JPEG
            if image.mode == 'RGBA' and image_format == 'JPEG':
                # Create a white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Save without metadata
            output = io.BytesIO()
            
            # Different save parameters for different formats
            if image_format == 'JPEG':
                image.save(output, format='JPEG', quality=95, optimize=True)
            elif image_format == 'PNG':
                image.save(output, format='PNG', optimize=True)
            else:
                image.save(output, format=image_format)
            
            output.seek(0)
            return output.read(), self.mime_type
            
        except Exception as e:
            raise Exception(f"Failed to remove image metadata: {str(e)}")
    
    def remove_pdf_metadata(self):
        """Remove metadata from PDF files"""
        try:
            import PyPDF2
            
            self.file_obj.seek(0)
            pdf_reader = PyPDF2.PdfReader(self.file_obj)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Don't add metadata
            # pdf_writer.add_metadata({})  # Empty metadata
            
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            return output.read(), self.mime_type
            
        except ImportError:
            raise Exception("PyPDF2 not installed")
        except Exception as e:
            raise Exception(f"Failed to remove PDF metadata: {str(e)}")
    
    def remove_docx_metadata(self):
        """Remove metadata from DOCX files"""
        try:
            from docx import Document
            
            self.file_obj.seek(0)
            doc = Document(self.file_obj)
            
            # Clear core properties
            core_props = doc.core_properties
            core_props.author = ''
            core_props.comments = ''
            core_props.keywords = ''
            core_props.last_modified_by = ''
            core_props.revision = 1
            core_props.subject = ''
            core_props.title = ''
            
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return output.read(), self.mime_type
            
        except ImportError:
            raise Exception("python-docx not installed")
        except Exception as e:
            raise Exception(f"Failed to remove DOCX metadata: {str(e)}")
    
    def remove_platform_specific(self, metadata_dict):
        """
        Remove metadata based on platform-specific rules
        This is used in conjunction with platform rules
        """
        from django.conf import settings
        
        if not self.platform or self.platform not in settings.PLATFORM_RULES:
            # Remove all metadata
            return self.remove()
        
        # For now, we remove all metadata
        # In future, you can implement selective removal based on platform rules
        return self.remove()