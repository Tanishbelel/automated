from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from .models import FileAnalysis, MetadataEntry, PlatformRule
from .serializers import (
    FileAnalysisSerializer, MetadataEntrySerializer,
    FileUploadSerializer, MetadataAnalysisResponseSerializer,
    CleanFileRequestSerializer, PlatformRuleSerializer
)
from .utils.metadata_extractor import MetadataExtractor
from .utils.metadata_remover import MetadataRemover
from .utils.risk_analyzer import RiskAnalyzer
import io

class FileAnalysisViewSet(viewsets.ModelViewSet):
    queryset = FileAnalysis.objects.all()
    serializer_class = FileAnalysisSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        return queryset


class AnalyzeFileView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        platform = serializer.validated_data['platform']
        
        file_analysis = FileAnalysis.objects.create(
            user=request.user if request.user.is_authenticated else None,
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
            platform=platform,
            status='pending'
        )
        
        try:
            metadata = MetadataExtractor.extract_metadata(uploaded_file, uploaded_file.content_type)
            
            metadata_entries = []
            for key, value in metadata.items():
                category = MetadataExtractor.categorize_metadata(key, value)
                risk_level = RiskAnalyzer.get_risk_level(category)
                
                entry = MetadataEntry.objects.create(
                    file_analysis=file_analysis,
                    key=key,
                    value=value,
                    category=category,
                    risk_level=risk_level
                )
                metadata_entries.append(entry)
            
            metadata_entries_data = [
                {
                    'key': e.key,
                    'value': e.value,
                    'category': e.category,
                    'risk_level': e.risk_level
                }
                for e in metadata_entries
            ]
            
            risk_score = RiskAnalyzer.calculate_risk_score(metadata_entries_data)
            
            file_analysis.metadata_count = len(metadata_entries)
            file_analysis.risk_score = risk_score
            file_analysis.status = 'analyzed'
            file_analysis.save()
            
            risk_recommendation = RiskAnalyzer.get_risk_recommendation(risk_score)
            
            response_data = {
                'analysis_id': file_analysis.id,
                'filename': file_analysis.original_filename,
                'file_type': file_analysis.file_type,
                'file_size': file_analysis.file_size,
                'platform': file_analysis.platform,
                'risk_score': risk_score,
                'metadata_count': len(metadata_entries),
                'metadata_entries': MetadataEntrySerializer(metadata_entries, many=True).data,
                'risk_recommendation': risk_recommendation
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            file_analysis.status = 'failed'
            file_analysis.save()
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CleanFileView(APIView):
    
    def post(self, request):
        serializer = CleanFileRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_id = serializer.validated_data['analysis_id']
        
        try:
            file_analysis = FileAnalysis.objects.get(id=analysis_id)
        except FileAnalysis.DoesNotExist:
            return Response(
                {'error': 'File analysis not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {'message': 'File cleaning requires original file upload'},
            status=status.HTTP_400_BAD_REQUEST
        )


class CleanAndDownloadView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        
        try:
            cleaned_file = MetadataRemover.remove_metadata(uploaded_file, uploaded_file.content_type)
            
            filename_parts = uploaded_file.name.rsplit('.', 1)
            if len(filename_parts) == 2:
                clean_filename = f"{filename_parts[0]}_clean.{filename_parts[1]}"
            else:
                clean_filename = f"{uploaded_file.name}_clean"
            
            response = FileResponse(
                cleaned_file,
                as_attachment=True,
                filename=clean_filename
            )
            response['Content-Type'] = uploaded_file.content_type
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Cleaning failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlatformRuleViewSet(viewsets.ModelViewSet):
    queryset = PlatformRule.objects.filter(is_active=True)
    serializer_class = PlatformRuleSerializer
    
    @action(detail=False, methods=['get'])
    def by_platform(self, request):
        platform = request.query_params.get('platform', 'general')
        try:
            rule = PlatformRule.objects.get(platform=platform, is_active=True)
            serializer = self.get_serializer(rule)
            return Response(serializer.data)
        except PlatformRule.DoesNotExist:
            return Response(
                {'risky_metadata_keys': RiskAnalyzer.get_platform_risky_keys(platform)},
                status=status.HTTP_200_OK
            )


class HealthCheckView(APIView):
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'Automated Metadata Removal API',
            'version': '1.0.0'
        })