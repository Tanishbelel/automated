import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class FileUploadValidationMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        if request.method == 'POST' and request.FILES:
            for file_key, uploaded_file in request.FILES.items():
                if uploaded_file.size > 52428800:
                    return JsonResponse({
                        'error': 'File size exceeds 50MB limit'
                    }, status=413)
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        logger.info(f'{request.method} {request.path} - User: {request.user}')
        return None
    
    def process_response(self, request, response):
        logger.info(f'{request.method} {request.path} - Status: {response.status_code}')
        return response


class CORSExtensionMiddleware(MiddlewareMixin):
    
    def process_response(self, request, response):
        origin = request.META.get('HTTP_ORIGIN', '')
        
        if origin.startswith('chrome-extension://') or origin.startswith('moz-extension://'):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
    
