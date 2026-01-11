from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils.batch_processor import BatchProcessor
from .serializers import FileUploadSerializer
import zipfile
import io

class BatchAnalyzeView(APIView):
    
    def post(self, request):
        files = request.FILES.getlist('files')
        platform = request.data.get('platform', 'general')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(files) > 20:
            return Response(
                {'error': 'Maximum 20 files allowed per batch'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user if request.user.is_authenticated else None
        
        results = BatchProcessor.process_multiple_files(files, platform, user)
        
        return Response({
            'total_files': len(files),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }, status=status.HTTP_200_OK)


class BatchCleanView(APIView):
    
    def post(self, request):
        files = request.FILES.getlist('files')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(files) > 20:
            return Response(
                {'error': 'Maximum 20 files allowed per batch'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cleaned_results = BatchProcessor.clean_multiple_files(files)
        
        if len(cleaned_results) == 1:
            result = cleaned_results[0]
            if result['status'] == 'success':
                from django.http import FileResponse
                return FileResponse(
                    result['file'],
                    as_attachment=True,
                    filename=f"clean_{result['filename']}"
                )
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result in cleaned_results:
                if result['status'] == 'success':
                    file_data = result['file'].read()
                    zip_file.writestr(f"clean_{result['filename']}", file_data)
        
        zip_buffer.seek(0)
        
        from django.http import FileResponse
        return FileResponse(
            zip_buffer,
            as_attachment=True,
            filename='cleaned_files.zip',
            content_type='application/zip'
        )