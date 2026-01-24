from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, StreamingHttpResponse
from django.core.files.base import ContentFile
from .models import FileAnalysis, MetadataEntry, PlatformRule
from .serializers import (
    FileAnalysisSerializer, MetadataEntrySerializer,
    FileUploadSerializer, PlatformRuleSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .utils.metadata_extractor import MetadataExtractor
from .utils.metadata_remover import MetadataRemover
from .utils.risk_analyzer import RiskAnalyzer
from .utils.qr_generator import QRCodeGenerator
import io
import os
import tempfile
from .utils.encryption_handler import EncryptionHandler, PasswordStrengthValidator
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, UpdateProfileSerializer
)
import requests
from django.conf import settings
import time

from .utils.google_auth import GoogleOAuth
from django.shortcuts import redirect

class GoogleLoginView(APIView):
    """
    Initiate Google OAuth login
    GET /api/auth/google/login/
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        auth_url = GoogleOAuth.get_google_auth_url()
        return Response({
            'auth_url': auth_url,
            'message': 'Redirect user to this URL'
        })


class GoogleCallbackView(APIView):
    """
    Google OAuth callback endpoint
    GET /api/auth/google/callback/?code=...
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        code = request.GET.get('code')
        
        if not code:
            return Response(
                {'error': 'Authorization code not provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for tokens
            token_data = GoogleOAuth.exchange_code_for_token(code)
            access_token = token_data.get('access_token')
            
            # Get user info from Google
            user_info = GoogleOAuth.get_user_info(access_token)
            
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            google_id = user_info.get('id')
            
            # Check if user exists
            user = User.objects.filter(email=email).first()
            
            if not user:
                # Create new user
                username = email.split('@')[0]
                
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                user.set_unusable_password()  # No password for OAuth users
                user.save()
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            
            # Redirect to frontend with token (adjust URL as needed)
            frontend_url = f"http://localhost:3000/auth/callback?token={token.key}"
            return redirect(frontend_url)
            
        except Exception as e:
            import traceback
            print("Google OAuth Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleLoginTokenView(APIView):
    """
    Verify Google ID token directly (for mobile/SPA)
    POST /api/auth/google/verify/
    Body: {id_token: "google_id_token"}
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        id_token_str = request.data.get('id_token')
        
        if not id_token_str:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify the token
            idinfo = GoogleOAuth.verify_google_token(id_token_str)
            
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            google_id = idinfo.get('sub')
            
            # Check if user exists
            user = User.objects.filter(email=email).first()
            
            if not user:
                # Create new user
                username = email.split('@')[0]
                
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                user.set_unusable_password()
                user.save()
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Google login successful'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print("Google Token Verification Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /api/auth/register/
    Body: {username, email, password, password2, first_name (optional), last_name (optional)}
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    User login endpoint
    POST /api/auth/login/
    Body: {username, password}
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Login user (creates session)
        login(request, user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    User logout endpoint
    POST /api/auth/logout/
    Headers: Authorization: Token <token>
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
        except Exception:
            pass
        
        # Logout user (destroys session)
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    Get current user profile
    GET /api/auth/profile/
    Headers: Authorization: Token <token>
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UpdateProfileView(generics.UpdateAPIView):
    """
    Update user profile
    PUT/PATCH /api/auth/profile/update/
    Headers: Authorization: Token <token>
    Body: {first_name, last_name, email}
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UpdateProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        })


class ChangePasswordView(APIView):
    """
    Change user password
    POST /api/auth/change-password/
    Headers: Authorization: Token <token>
    Body: {old_password, new_password, new_password2}
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # Update token
            Token.objects.filter(user=request.user).delete()
            token = Token.objects.create(user=request.user)
            
            return Response({
                'message': 'Password changed successfully',
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    """
    Delete user account
    DELETE /api/auth/delete-account/
    Headers: Authorization: Token <token>
    Body: {password}
    """
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required to delete account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(password):
            return Response(
                {'error': 'Incorrect password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete user account
        user = request.user
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)
    
def file_iterator(file_object, chunk_size=8192):
    """Generator to read file in chunks to avoid memory issues."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


class FileAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = FileAnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FileAnalysis.objects.filter(user=self.request.user)

    
    @action(detail=True, methods=['get'])
    def download_clean(self, request, pk=None):
        file_analysis = self.get_object()
        
        if not file_analysis.cleaned_file:
            return Response(
                {'error': 'Cleaned file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check file size for streaming
        file_size = file_analysis.cleaned_file.size
        
        if file_size > 10 * 1024 * 1024:  # > 10MB, use streaming
            response = StreamingHttpResponse(
                file_iterator(file_analysis.cleaned_file.open('rb')),
                content_type=file_analysis.file_type
            )
            response['Content-Disposition'] = f'attachment; filename="clean_{file_analysis.original_filename}"'
            response['Content-Length'] = file_size
        else:
            response = FileResponse(
                file_analysis.cleaned_file.open('rb'),
                as_attachment=True,
                filename=f"clean_{file_analysis.original_filename}"
            )
            response['Content-Length'] = file_size
        
        return response
    
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
        
        # ---------- VIRUSTOTAL VALIDATION (PRE-CHECK) ----------
        print("🔍 VirusTotal pre-scan started for:", uploaded_file.name)

        vt_response = requests.post(
            "https://www.virustotal.com/api/v3/files",
            headers={
                "x-apikey": settings.VIRUSTOTAL_API_KEY
            },
            files={
                "file": (uploaded_file.name, uploaded_file.read())
            }
        )

        print("✅ VirusTotal upload status:", vt_response.status_code)

        if vt_response.status_code != 200:
            return Response(
                {"error": "Virus scanning service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        analysis_id = vt_response.json()["data"]["id"]
        print("🆔 VirusTotal analysis_id:", analysis_id)

        time.sleep(5)

        analysis_response = requests.get(
            f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
            headers={
                "x-apikey": settings.VIRUSTOTAL_API_KEY
            }
        )

        stats = analysis_response.json()["data"]["attributes"]["stats"]
        print("📊 VirusTotal result:", stats)

        if stats.get("malicious", 0) > 0:
            print("🚫 File blocked by VirusTotal")
            return Response(
                {
                    "status": "blocked",
                    "reason": "Malicious file detected",
                    "scan_result": stats
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        print("✅ VirusTotal check passed, continuing main logic")

        # ---------- END VIRUSTOTAL PRE-CHECK ----------

        file_analysis = None
        temp_file = None
        
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
            
            # For large files (> 10MB), use temporary storage
            is_large_file = uploaded_file.size > 10 * 1024 * 1024
            
            if is_large_file:
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=os.path.splitext(uploaded_file.name)[1]
                )
                
                # Save uploaded file to temp in chunks
                for chunk in uploaded_file.chunks(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()
                
                # Save to model from temp file
                with open(temp_file.name, 'rb') as f:
                    file_analysis.original_file.save(uploaded_file.name, f, save=True)
                
                # Extract metadata from temp file
                with open(temp_file.name, 'rb') as f:
                    metadata = MetadataExtractor.extract_metadata(f, uploaded_file.content_type)
            else:
                # For smaller files, process directly
                uploaded_file.seek(0)
                file_analysis.original_file.save(uploaded_file.name, uploaded_file, save=True)
                
                uploaded_file.seek(0)
                metadata = MetadataExtractor.extract_metadata(uploaded_file, uploaded_file.content_type)
            
            # Create metadata entries
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
            
            # Calculate risk with improved algorithm
            metadata_data = [{'category': e.category} for e in metadata_entries]
            risk_score = RiskAnalyzer.calculate_risk_score(metadata_data)
            
            # Remove metadata
            if is_large_file and temp_file:
                with open(temp_file.name, 'rb') as f:
                    cleaned = MetadataRemover.remove_metadata(
                        f, 
                        uploaded_file.content_type,
                        uploaded_file.name
                    )
            else:
                uploaded_file.seek(0)
                cleaned = MetadataRemover.remove_metadata(
                    uploaded_file, 
                    uploaded_file.content_type,
                    uploaded_file.name
                )
            
            # Save cleaned file
            filename_parts = uploaded_file.name.rsplit('.', 1)
            if len(filename_parts) == 2:
                clean_name = f"{filename_parts[0]}_clean.{filename_parts[1]}"
            else:
                clean_name = f"{uploaded_file.name}_clean"
            
            if hasattr(cleaned, 'seek'):
                cleaned.seek(0)
            
            file_analysis.cleaned_file.save(clean_name, cleaned, save=False)
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
        
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


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
        
        file_size = file_analysis.cleaned_file.size
        
        # Use streaming for large files
        if file_size > 10 * 1024 * 1024:  # > 10MB
            response = StreamingHttpResponse(
                file_iterator(file_analysis.cleaned_file.open('rb')),
                content_type=file_analysis.file_type
            )
            response['Content-Disposition'] = f'attachment; filename="clean_{file_analysis.original_filename}"'
            response['Content-Length'] = file_size
        else:
            response = FileResponse(
                file_analysis.cleaned_file.open('rb'),
                as_attachment=True,
                filename=f"clean_{file_analysis.original_filename}"
            )
            response['Content-Length'] = file_size
        
        return response


class CleanAndDownloadView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        temp_file = None
        
        try:
            is_large_file = uploaded_file.size > 10 * 1024 * 1024
            
            # Process large files using temp storage
            if is_large_file:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(uploaded_file.name)[1]
                )
                
                # Write to temp file in chunks
                for chunk in uploaded_file.chunks(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()
                
                # Process from temp file
                with open(temp_file.name, 'rb') as f:
                    cleaned_file = MetadataRemover.remove_metadata(
                        f, 
                        uploaded_file.content_type,
                        uploaded_file.name
                    )
            else:
                # Process smaller files directly
                uploaded_file.seek(0)
                cleaned_file = MetadataRemover.remove_metadata(
                    uploaded_file, 
                    uploaded_file.content_type,
                    uploaded_file.name
                )
            
            # Generate clean filename
            filename_parts = uploaded_file.name.rsplit('.', 1)
            if len(filename_parts) == 2:
                clean_filename = f"{filename_parts[0]}_clean.{filename_parts[1]}"
            else:
                clean_filename = f"{uploaded_file.name}_clean"
            
            # Ensure file is at beginning
            if hasattr(cleaned_file, 'seek'):
                cleaned_file.seek(0)
            
            # Use streaming response for large files
            if is_large_file and hasattr(cleaned_file, 'size'):
                response = StreamingHttpResponse(
                    file_iterator(cleaned_file),
                    content_type=uploaded_file.content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{clean_filename}"'
                response['Content-Length'] = cleaned_file.size
            else:
                response = FileResponse(
                    cleaned_file,
                    as_attachment=True,
                    filename=clean_filename
                )
                response['Content-Type'] = uploaded_file.content_type
                
                if hasattr(cleaned_file, 'size'):
                    response['Content-Length'] = cleaned_file.size
            
            return response
            
        except Exception as e:
            import traceback
            print("Cleaning Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': f'Cleaning failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


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
        
        file_size = file_analysis.cleaned_file.size
        
        # Use streaming for large files
        if file_size > 10 * 1024 * 1024:  # > 10MB
            response = StreamingHttpResponse(
                file_iterator(file_analysis.cleaned_file.open('rb')),
                content_type=file_analysis.file_type
            )
            response['Content-Disposition'] = f'attachment; filename="clean_{file_analysis.original_filename}"'
            response['Content-Length'] = file_size
        else:
            response = FileResponse(
                file_analysis.cleaned_file.open('rb'),
                as_attachment=True,
                filename=f"clean_{file_analysis.original_filename}"
            )
            response['Content-Length'] = file_size
        
        return response


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
        method = request.data.get('method', 'encrypt')
        temp_file = None
        
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
            is_large_file = uploaded_file.size > 10 * 1024 * 1024
            
            # Handle large files with temp storage
            if is_large_file:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(uploaded_file.name)[1]
                )
                
                for chunk in uploaded_file.chunks(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()
                
                with open(temp_file.name, 'rb') as f:
                    encrypted_file = EncryptionHandler.protect_file(
                        f,
                        uploaded_file.name,
                        password,
                        method
                    )
            else:
                uploaded_file.seek(0)
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
            
            if hasattr(encrypted_file, 'seek'):
                encrypted_file.seek(0)
            
            # Use streaming for large encrypted files
            if is_large_file and hasattr(encrypted_file, 'size') and encrypted_file.size > 10 * 1024 * 1024:
                response = StreamingHttpResponse(
                    file_iterator(encrypted_file),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{encrypted_filename}"'
                response['Content-Length'] = encrypted_file.size
            else:
                response = FileResponse(
                    encrypted_file,
                    as_attachment=True,
                    filename=encrypted_filename
                )
                
                if hasattr(encrypted_file, 'size'):
                    response['Content-Length'] = encrypted_file.size
            
            return response
        
        except Exception as e:
            import traceback
            print("Encryption Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': f'Encryption failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


class DecryptFileView(APIView):
    """Decrypt password-protected files"""
    
    def post(self, request):
        uploaded_file = request.FILES.get('file')
        password = request.data.get('password')
        original_filename = request.data.get('original_filename', '')
        temp_file = None
        
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
            is_large_file = uploaded_file.size > 10 * 1024 * 1024
            
            # Handle large files with temp storage
            if is_large_file:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(uploaded_file.name)[1]
                )
                
                for chunk in uploaded_file.chunks(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()
                
                with open(temp_file.name, 'rb') as f:
                    decrypted_file = EncryptionHandler.decrypt_file(f, password)
            else:
                uploaded_file.seek(0)
                decrypted_file = EncryptionHandler.decrypt_file(uploaded_file, password)
            
            # Determine filename
            if original_filename:
                filename = original_filename
            else:
                uploaded_name = uploaded_file.name
                
                if uploaded_name.endswith('_encrypted.enc'):
                    filename = uploaded_name.replace('_encrypted.enc', '')
                elif uploaded_name.endswith('.enc'):
                    filename = uploaded_name.replace('.enc', '')
                elif uploaded_name.endswith('_protected.zip'):
                    filename = uploaded_name.replace('_protected.zip', '')
                elif uploaded_name.endswith('_protected.pdf'):
                    filename = uploaded_name.replace('_protected.pdf', '.pdf')
                else:
                    filename = uploaded_name.replace('_protected', '_decrypted')
            
            if hasattr(decrypted_file, 'seek'):
                decrypted_file.seek(0)
            
            # Use streaming for large decrypted files
            if is_large_file and hasattr(decrypted_file, 'size') and decrypted_file.size > 10 * 1024 * 1024:
                response = StreamingHttpResponse(
                    file_iterator(decrypted_file),
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = decrypted_file.size
            else:
                response = FileResponse(
                    decrypted_file,
                    as_attachment=True,
                    filename=filename
                )
                
                if hasattr(decrypted_file, 'size'):
                    response['Content-Length'] = decrypted_file.size
            
            return response
        
        except Exception as e:
            import traceback
            print("Decryption Error:", str(e))
            print(traceback.format_exc())
            
            return Response(
                {'error': 'Decryption failed: Wrong password or corrupted file'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass


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