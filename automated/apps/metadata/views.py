# apps/metadata/views.py
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.utils import timezone
import time
import io
import json

from .models import FileAnalysis, PlatformRule, ProcessingLog
from .serializers import (
    FileUploadSerializer, MetadataAnalysisResponseSerializer,
    MetadataRemovalRequestSerializer, PlatformRuleSerializer,
    FileAnalysisSerializer, PlatformListSerializer
)
from .services.metadata_extractor import MetadataExtractor
from .services.metadata_remover import MetadataRemover
from .services.risk_analyzer import RiskAnalyzer
from .services.platform_rules import PlatformRules


class MetadataAnalysisView(APIView):
    """API endpoint for analyzing file metadata"""
    
    def post(self, request):
        """Analyze uploaded file for metadata"""
        start_time = time.time()
        
        # Validate input
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        
        try:
            # Extract metadata
            extractor = MetadataExtractor(file_obj, file_obj.name)
            metadata = extractor.extract()
            
            # Analyze risks
            analyzer = RiskAnalyzer(metadata)
            risk_analysis = analyzer.analyze()
            recommendations = analyzer.get_recommendations(risk_analysis['risk_level'])
            
            # Platform-specific analysis if platform specified
            platform_risk = None
            if platform:
                platform_risk = analyzer.analyze_for_platform(platform)
            
            # Create file analysis record
            file_analysis = FileAnalysis.objects.create(
                file_name=file_obj.name,
                file_type=metadata['file_info'].get('mime_type', 'unknown'),
                file_size=metadata['file_info'].get('size', 0),
                risk_score=risk_analysis['risk_score'],
                risk_level=risk_analysis['risk_level'],
                has_gps=risk_analysis['has_gps'],
                has_camera_info=risk_analysis['has_camera_info'],
                has_author_info=risk_analysis['has_author_info'],
                has_software_info=risk_analysis['has_software_info'],
                target_platform=platform if platform else None,
            )
            file_analysis.set_metadata_before(metadata)
            
            # Log the analysis
            processing_time = int((time.time() - start_time) * 1000)
            file_analysis.save()  # Save after setting metadata
            
            ProcessingLog.objects.create(
                file_analysis=file_analysis,
                action='analyze',
                status='success',
                message='File analyzed successfully',
                processing_time_ms=processing_time
            )
            
            # Prepare response
            response_data = {
                'analysis_id': file_analysis.id,
                'file_name': file_obj.name,
                'file_type': metadata['file_info'].get('mime_type', 'unknown'),
                'file_size': metadata['file_info'].get('size', 0),
                'risk_score': risk_analysis['risk_score'],
                'risk_level': risk_analysis['risk_level'],
                'risk_factors': risk_analysis['risk_factors'],
                'recommendations': recommendations,
                'metadata': metadata,
                'has_gps': risk_analysis['has_gps'],
                'has_camera_info': risk_analysis['has_camera_info'],
                'has_author_info': risk_analysis['has_author_info'],
                'has_software_info': risk_analysis['has_software_info'],
                'platform': platform,
                'platform_risk': platform_risk,
                'processing_time_ms': processing_time,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log error
            ProcessingLog.objects.create(
                file_analysis=FileAnalysis.objects.create(
                    file_name=file_obj.name,
                    file_type='unknown',
                    file_size=0,
                ),
                action='analyze',
                status='error',
                message='Analysis failed',
                error_details=str(e)
            )
            
            return Response(
                {'error': f'Failed to analyze file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MetadataRemovalView(APIView):
    """API endpoint for removing metadata from files"""
    
    def post(self, request):
        """Remove metadata and return cleaned file"""
        start_time = time.time()
        
        # Validate input
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        
        try:
            # Remove metadata
            remover = MetadataRemover(file_obj, file_obj.name, platform)
            cleaned_data, mime_type = remover.remove()
            
            # Extract metadata from cleaned file to verify
            cleaned_file = io.BytesIO(cleaned_data)
            extractor = MetadataExtractor(cleaned_file, file_obj.name)
            metadata_after = extractor.extract()
            
            # Analyze cleaned file
            analyzer = RiskAnalyzer(metadata_after)
            risk_after = analyzer.analyze()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Return cleaned file
            response = HttpResponse(cleaned_data, content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename="clean_{file_obj.name}"'
            response['X-Processing-Time'] = str(processing_time)
            response['X-Risk-Score-After'] = str(risk_after['risk_score'])
            response['X-Risk-Level-After'] = risk_after['risk_level']
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to remove metadata: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchMetadataRemovalView(APIView):
    """API endpoint for batch metadata removal"""
    
    def post(self, request):
        """Remove metadata from multiple files"""
        files = request.FILES.getlist('files')
        platform = request.data.get('platform', 'general')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        
        for file_obj in files:
            try:
                remover = MetadataRemover(file_obj, file_obj.name, platform)
                cleaned_data, mime_type = remover.remove()
                
                results.append({
                    'file_name': file_obj.name,
                    'status': 'success',
                    'size_before': file_obj.size,
                    'size_after': len(cleaned_data),
                })
                
            except Exception as e:
                results.append({
                    'file_name': file_obj.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return Response({
            'total_files': len(files),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': results
        })


class PlatformRulesView(APIView):
    """API endpoint for platform rules"""
    
    def get(self, request):
        """Get list of all platforms and their rules"""
        platforms = PlatformRules.get_all_platforms()
        
        # Add detailed rules for each platform
        for platform in platforms:
            rules = PlatformRules(platform['name'])
            platform['rules'] = rules.get_platform_info()
        
        return Response({
            'platforms': platforms,
            'total': len(platforms)
        })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'Metadata Removal API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
def supported_formats(request):
    """Get list of supported file formats"""
    from django.conf import settings
    
    return Response({
        'formats': settings.SUPPORTED_FILE_FORMATS,
        'total_formats': sum(len(formats) for formats in settings.SUPPORTED_FILE_FORMATS.values())
    })