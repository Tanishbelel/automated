from PIL import Image
import io
from django.core.files.base import ContentFile


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
    def remove_metadata(file_obj, file_type):
        if 'jpeg' in file_type.lower() or 'jpg' in file_type.lower():
            return MetadataRemover.remove_from_image(file_obj, 'JPEG')
        elif 'png' in file_type.lower():
            return MetadataRemover.remove_from_image(file_obj, 'PNG')
        else:
            return MetadataRemover.remove_from_image(file_obj, 'JPEG')
    
    @staticmethod
    def remove_selective_metadata(file_obj, file_type, keys_to_remove):
        return MetadataRemover.remove_metadata(file_obj, file_type)