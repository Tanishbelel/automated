from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from django.core.files.base import ContentFile
from .models import FileAnalysis, MetadataEntry, PlatformRule
from .serializers import (
    FileAnalysisSerializer, MetadataEntrySerializer,
    FileUploadSerializer, PlatformRuleSerializer
)
from .utils.metadata_extractor import MetadataExtractor
from .utils.metadata_remover import MetadataRemover
from .utils.risk_analyzer import RiskAnalyzer
from .utils.qr_generator import QRCodeGenerator
import io
from .utils.encryption_handler import EncryptionHandler, PasswordStrengthValidator


class FileAnalysisViewSet(viewsets.ModelViewSet):
    queryset = FileAnalysis.objects.all()
    serializer_class = FileAnalysisSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    @action(detail=True, methods=['get'])
    def download_clean(self, request, pk=None):
        file_analysis = self.get_object()
        
        if not file_analysis.cleaned_file:
            return Response(
                {'error': 'Cleaned file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            file_analysis.cleaned_file.open('rb'),
            as_attachment=True,
            filename=f"clean_{file_analysis.original_filename}"
        )
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        file_analysis = self.get_object()
        
        share_url = request.build_absolute_uri(f'/share/{file_analysis.share_token}/')
        qr_image = QRCodeGenerator.generate_qr_code(share_url)
        
        return FileResponse(
            qr_image,
            as_attachment=True,
            filename=f"qr_{file_analysis.id}.png",
            content_type='image/png'
        )


class AnalyzeFileView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        
        file_analysis = None
        
        try:
            # Create record
            file_analysis = FileAnalysis.objects.create(
                user=request.user if request.user.is_authenticated else None,
                original_filename=uploaded_file.name,
                file_type=uploaded_file.content_type,
                file_size=uploaded_file.size,
                platform=platform,
                status='pending'
            )
            
            # Save original
            file_analysis.original_file.save(uploaded_file.name, uploaded_file)
            
            # Extract metadata
            uploaded_file.seek(0)
            metadata = MetadataExtractor.extract_metadata(uploaded_file, uploaded_file.content_type)
            
            # Create entries
            metadata_entries = []
            for key, value in metadata.items():
                category = MetadataExtractor.categorize_metadata(key, value)
                risk_level = RiskAnalyzer.get_risk_level(category)
                
                entry = MetadataEntry.objects.create(
                    file_analysis=file_analysis,
                    key=str(key),
                    value=str(value)[:500],
                    category=category,
                    risk_level=risk_level
                )
                metadata_entries.append(entry)
            
            # Calculate risk
            metadata_data = [{'category': e.category} for e in metadata_entries]
            risk_score = RiskAnalyzer.calculate_risk_score(metadata_data)
            
            # Remove metadata - UPDATED LINE
            uploaded_file.seek(0)
            cleaned = MetadataRemover.remove_metadata(
                uploaded_file, 
                uploaded_file.content_type,
                uploaded_file.name  # Pass the original filename
            )
            
            # Save cleaned
            clean_name = f"{uploaded_file.name.rsplit('.', 1)[0]}_clean.{uploaded_file.name.rsplit('.', 1)[1]}"
            file_analysis.cleaned_file.save(clean_name, cleaned)
            file_analysis.metadata_count = len(metadata_entries)
            file_analysis.risk_score = risk_score
            file_analysis.status = 'cleaned'
            file_analysis.save()
            
            return Response({
                'analysis_id': str(file_analysis.id),
                'filename': file_analysis.original_filename,
                'file_type': file_analysis.file_type,
                'file_size': file_analysis.file_size,
                'platform': file_analysis.platform,
                'risk_score': risk_score,
                'metadata_count': len(metadata_entries),
                'metadata_entries': MetadataEntrySerializer(metadata_entries, many=True).data,
                'risk_recommendation': RiskAnalyzer.get_risk_recommendation(risk_score),
                'share_token': str(file_analysis.share_token)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            if file_analysis:
                file_analysis.status = 'failed'
                file_analysis.save()
            
            import traceback
            print("ERROR:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CleanFileView(APIView):
    
    def post(self, request):
        analysis_id = request.data.get('analysis_id')
        
        if not analysis_id:
            return Response(
                {'error': 'analysis_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            file_analysis = FileAnalysis.objects.get(id=analysis_id)
        except FileAnalysis.DoesNotExist:
            return Response(
                {'error': 'File analysis not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not file_analysis.cleaned_file:
            return Response(
                {'error': 'Cleaned file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            file_analysis.cleaned_file.open('rb'),
            as_attachment=True,
            filename=f"clean_{file_analysis.original_filename}"
        )


class CleanAndDownloadView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        
        try:
            # UPDATED LINE - Pass the original filename
            cleaned_file = MetadataRemover.remove_metadata(
                uploaded_file, 
                uploaded_file.content_type,
                uploaded_file.name  # Pass the original filename
            )
            
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


class ShareFileView(APIView):
    
    def get(self, request, share_token):
        try:
            file_analysis = FileAnalysis.objects.get(share_token=share_token)
        except FileAnalysis.DoesNotExist:
            return Response(
                {'error': 'File not found or link expired'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = FileAnalysisSerializer(file_analysis, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, share_token):
        try:
            file_analysis = FileAnalysis.objects.get(share_token=share_token)
        except FileAnalysis.DoesNotExist:
            return Response(
                {'error': 'File not found or link expired'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not file_analysis.cleaned_file:
            return Response(
                {'error': 'Cleaned file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            file_analysis.cleaned_file.open('rb'),
            as_attachment=True,
            filename=f"clean_{file_analysis.original_filename}"
        )


class MakePublicView(APIView):
    
    def post(self, request, pk):
        try:
            file_analysis = FileAnalysis.objects.get(id=pk)
        except FileAnalysis.DoesNotExist:
            return Response(
                {'error': 'File analysis not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.user.is_authenticated and file_analysis.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        file_analysis.is_public = True
        file_analysis.save()
        
        share_url = request.build_absolute_uri(f'/share/{file_analysis.share_token}/')
        
        return Response({
            'share_token': str(file_analysis.share_token),
            'share_url': share_url,
            'is_public': file_analysis.is_public
        })


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
    



class EncryptFileView(APIView):
    """Encrypt and password-protect files"""
    
    def post(self, request):
        uploaded_file = request.FILES.get('file')
        password = request.data.get('password')
        method = request.data.get('method', 'encrypt')  # 'encrypt', 'pdf', or 'zip'
        
        if not uploaded_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Encrypt the file
            encrypted_file = EncryptionHandler.protect_file(
                uploaded_file,
                uploaded_file.name,
                password,
                method
            )
            
            # Generate encrypted filename
            name_parts = uploaded_file.name.rsplit('.', 1)
            if method == 'zip':
                encrypted_filename = f"{name_parts[0]}_protected.zip"
            elif method == 'encrypt':
                encrypted_filename = f"{name_parts[0]}_encrypted.enc"
            else:
                encrypted_filename = f"{name_parts[0]}_protected.{name_parts[1] if len(name_parts) > 1 else 'pdf'}"
            
            response = FileResponse(
                encrypted_file,
                as_attachment=True,
                filename=encrypted_filename
            )
            
            return response
        
        except Exception as e:
            import traceback
            print("Encryption Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': f'Encryption failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DecryptFileView(APIView):
    """Decrypt password-protected files"""
    
    def post(self, request):
        uploaded_file = request.FILES.get('file')
        password = request.data.get('password')
        original_filename = request.data.get('original_filename', '')  # Optional: user can provide original name
        
        if not uploaded_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decrypt the file
            decrypted_file = EncryptionHandler.decrypt_file(uploaded_file, password)
            
            # Try to determine original filename
            if original_filename:
                # User provided the original filename
                filename = original_filename
            else:
                # Try to extract from uploaded filename
                uploaded_name = uploaded_file.name
                
                # Remove common encryption suffixes
                if uploaded_name.endswith('_encrypted.enc'):
                    filename = uploaded_name.replace('_encrypted.enc', '')
                elif uploaded_name.endswith('.enc'):
                    filename = uploaded_name.replace('.enc', '')
                elif uploaded_name.endswith('_protected.zip'):
                    filename = uploaded_name.replace('_protected.zip', '')
                elif uploaded_name.endswith('_protected.pdf'):
                    filename = uploaded_name.replace('_protected.pdf', '.pdf')
                else:
                    # Default: remove _protected or add _decrypted
                    filename = uploaded_name.replace('_protected', '_decrypted')
            
            response = FileResponse(
                decrypted_file,
                as_attachment=True,
                filename=filename
            )
            
            return response
        
        except Exception as e:
            import traceback
            print("Decryption Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': 'Decryption failed: Wrong password or corrupted file'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class ValidatePasswordView(APIView):
    """Validate password strength"""
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validation = PasswordStrengthValidator.validate_password(password)
        
        return Response(validation)