from PIL import Image
import io
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from pptx import Presentation
import subprocess
import tempfile
import os

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

class MetadataRemover:
    
    @staticmethod
    def remove_from_image(file_obj, file_format='JPEG'):
        file_obj.seek(0)
        image = Image.open(file_obj)
        
        # Convert to RGB if needed for JPEG
        if file_format.upper() in ['JPEG', 'JPG']:
            if image.mode in ['RGBA', 'LA', 'P']:
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, (0, 0), image if image.mode in ['RGBA', 'LA'] else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        
        # Save without metadata
        output = io.BytesIO()
        image.save(output, format=file_format, quality=95 if file_format == 'JPEG' else None)
        output.seek(0)
        
        return ContentFile(output.read())
    
    @staticmethod
    def remove_from_pdf(file_obj):
        """Remove metadata from PDF files"""
        try:
            file_obj.seek(0)
            pdf_reader = PdfReader(file_obj)
            pdf_writer = PdfWriter()
            
            # Copy all pages without metadata
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Explicitly remove metadata
            pdf_writer.add_metadata({})
            
            # Write to bytes
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            return ContentFile(output.read())
        except Exception as e:
            raise Exception(f"Error removing PDF metadata: {str(e)}")
    
    @staticmethod
    def remove_from_docx(file_obj):
        """Remove metadata from DOCX files"""
        try:
            file_obj.seek(0)
            doc = Document(file_obj)
            
            # Clear core properties (metadata)
            core_properties = doc.core_properties
            core_properties.author = ''
            core_properties.category = ''
            core_properties.comments = ''
            core_properties.content_status = ''
            core_properties.created = None
            core_properties.identifier = ''
            core_properties.keywords = ''
            core_properties.language = ''
            core_properties.last_modified_by = ''
            core_properties.last_printed = None
            core_properties.modified = None
            core_properties.revision = 1
            core_properties.subject = ''
            core_properties.title = ''
            core_properties.version = ''
            
            # Save to bytes
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return ContentFile(output.read())
        except Exception as e:
            raise Exception(f"Error removing DOCX metadata: {str(e)}")
    
    @staticmethod
    def remove_from_pptx(file_obj):
        """Remove metadata from PPTX files"""
        try:
            file_obj.seek(0)
            prs = Presentation(file_obj)
            
            # Clear core properties (metadata)
            core_properties = prs.core_properties
            core_properties.author = ''
            core_properties.category = ''
            core_properties.comments = ''
            core_properties.content_status = ''
            core_properties.created = None
            core_properties.identifier = ''
            core_properties.keywords = ''
            core_properties.language = ''
            core_properties.last_modified_by = ''
            core_properties.last_printed = None
            core_properties.modified = None
            core_properties.revision = 1
            core_properties.subject = ''
            core_properties.title = ''
            core_properties.version = ''
            
            # Save to bytes
            output = io.BytesIO()
            prs.save(output)
            output.seek(0)
            
            return ContentFile(output.read())
        except Exception as e:
            raise Exception(f"Error removing PPTX metadata: {str(e)}")
    
    @staticmethod
    def remove_from_video(file_obj, original_filename):
        """Remove metadata from video files using ffmpeg"""
        try:
            file_obj.seek(0)
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as temp_input:
                temp_input.write(file_obj.read())
                temp_input_path = temp_input.name
            
            temp_output_path = temp_input_path.replace(os.path.splitext(original_filename)[1], 
                                                       f'_cleaned{os.path.splitext(original_filename)[1]}')
            
            try:
                # Use ffmpeg to strip metadata
                subprocess.run([
                    'ffmpeg',
                    '-i', temp_input_path,
                    '-map_metadata', '-1',  # Remove all metadata
                    '-c:v', 'copy',  # Copy video codec (no re-encoding)
                    '-c:a', 'copy',  # Copy audio codec (no re-encoding)
                    '-y',  # Overwrite output file
                    temp_output_path
                ], check=True, capture_output=True)
                
                # Read cleaned video
                with open(temp_output_path, 'rb') as f:
                    cleaned_video = f.read()
                
                return ContentFile(cleaned_video)
            
            finally:
                # Clean up temporary files
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
        
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error removing video metadata with ffmpeg: {e.stderr.decode()}")
        except Exception as e:
            raise Exception(f"Error removing video metadata: {str(e)}")
    
    @staticmethod
    def remove_metadata(file_obj, file_type, original_filename=None):
        """Main method to route to appropriate handler"""
        file_type_lower = file_type.lower()
        
        # Images
        if 'jpeg' in file_type_lower or 'jpg' in file_type_lower:
            return MetadataRemover.remove_from_image(file_obj, 'JPEG')
        elif 'png' in file_type_lower:
            return MetadataRemover.remove_from_image(file_obj, 'PNG')
        elif 'gif' in file_type_lower:
            return MetadataRemover.remove_from_image(file_obj, 'GIF')
        elif 'bmp' in file_type_lower:
            return MetadataRemover.remove_from_image(file_obj, 'BMP')
        elif 'webp' in file_type_lower:
            return MetadataRemover.remove_from_image(file_obj, 'WEBP')
        
        # Documents
        elif 'pdf' in file_type_lower:
            return MetadataRemover.remove_from_pdf(file_obj)
        elif 'wordprocessingml' in file_type_lower or 'docx' in file_type_lower:
            return MetadataRemover.remove_from_docx(file_obj)
        elif 'presentationml' in file_type_lower or 'pptx' in file_type_lower:
            return MetadataRemover.remove_from_pptx(file_obj)
        
        # Videos
        elif any(video_type in file_type_lower for video_type in ['video', 'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv']):
            if not original_filename:
                raise ValueError("Original filename required for video processing")
            return MetadataRemover.remove_from_video(file_obj, original_filename)
        
        else:
            # Default fallback for unknown image types
            try:
                return MetadataRemover.remove_from_image(file_obj, 'JPEG')
            except:
                raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def remove_selective_metadata(file_obj, file_type, keys_to_remove, original_filename=None):
        """Remove metadata (currently removes all metadata for all file types)"""
        return MetadataRemover.remove_metadata(file_obj, file_type, original_filename)