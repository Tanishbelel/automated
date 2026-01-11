from PIL import Image
import io

class MetadataRemover:
    
    @staticmethod
    def remove_from_image(file_obj, file_format='JPEG'):
        try:
            file_obj.seek(0)
            image = Image.open(file_obj)
            
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            
            output = io.BytesIO()
            
            save_kwargs = {}
            if file_format.upper() in ['JPEG', 'JPG']:
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
                file_format = 'JPEG'
            elif file_format.upper() == 'PNG':
                save_kwargs['optimize'] = True
            
            image_without_exif.save(output, format=file_format, **save_kwargs)
            output.seek(0)
            
            return output
            
        except Exception as e:
            raise Exception(f"Failed to remove metadata: {str(e)}")
    
    @staticmethod
    def remove_metadata(file_obj, file_type):
        if file_type.startswith('image/'):
            format_map = {
                'image/jpeg': 'JPEG',
                'image/jpg': 'JPEG',
                'image/png': 'PNG',
                'image/gif': 'GIF',
                'image/webp': 'WEBP',
                'image/tiff': 'TIFF',
            }
            
            file_format = format_map.get(file_type.lower(), 'JPEG')
            return MetadataRemover.remove_from_image(file_obj, file_format)
        
        return file_obj
    
    @staticmethod
    def remove_selective_metadata(file_obj, file_type, keys_to_remove):
        if not keys_to_remove:
            return MetadataRemover.remove_metadata(file_obj, file_type)
        
        return MetadataRemover.remove_metadata(file_obj, file_type)