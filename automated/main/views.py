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

    @action(detail=True, methods=['post'])
    def secure_share(self, request, pk=None):
        file_analysis = self.get_object()
        duration_hours = int(request.data.get('duration_hours', 24))
        
        from django.utils import timezone
        import datetime
        
        file_analysis.is_public = True
        file_analysis.share_expiry = timezone.now() + datetime.timedelta(hours=duration_hours)
        file_analysis.save()
        
        share_url = request.build_absolute_uri(f'/api/share/{file_analysis.share_token}/')
        
        return Response({
            'share_url': share_url,
            'expiry': file_analysis.share_expiry,
            'message': f'Secure link generated, expires in {duration_hours} hours'
        })


class AnalyzeFileView(APIView):
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        
        # ---------- VIRUSTOTAL VALIDATION (PRE-CHECK) ----------
        if getattr(settings, 'VIRUSTOTAL_API_KEY', ''):
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
        
        uploaded_file.seek(0)
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
            
            # 3. Redact PII for images and PDFs
            mime = uploaded_file.content_type or ''
            from redaction.utils import is_image_mime, is_pdf_mime
            
            if is_image_mime(mime) or is_pdf_mime(mime):
                from redaction.detector import detect_sensitive_regions
                from redaction.redactor import redact_image
                from redaction.utils import pdf_to_images, images_to_pdf_bytes, image_to_png_bytes
                from PIL import Image
                import io
                from django.core.files.base import ContentFile
                
                try:
                    # Load the already metadata-stripped content
                    if hasattr(cleaned, 'read'):
                        cleaned.seek(0)
                        img_data = cleaned.read()
                    else:
                        img_data = cleaned
                    
                    if is_pdf_mime(mime):
                        print(f"📄 View: Redacting PDF {uploaded_file.name}...")
                        pages = pdf_to_images(img_data)
                        redacted_pages = []
                        for page_img in pages:
                            dets = detect_sensitive_regions(page_img)
                            redacted_pages.append(redact_image(page_img, dets))
                        out_bytes = images_to_pdf_bytes(redacted_pages)
                        cleaned = ContentFile(out_bytes)
                    else:
                        image = Image.open(io.BytesIO(img_data))
                        print(f"🖼️ View: Redacting Image {uploaded_file.name}...")
                        detections = detect_sensitive_regions(image)
                        if detections:
                            redacted_image = redact_image(image, detections)
                            out_bytes = image_to_png_bytes(redacted_image)
                            cleaned = ContentFile(out_bytes)
                            print(f"✅ View: Redaction applied.")
                except Exception as e:
                    print(f"⚠️ View: Redaction error: {str(e)}")

            if hasattr(cleaned, 'seek'):
                cleaned.seek(0)
            
            # Save cleaned file
            filename_parts = uploaded_file.name.rsplit('.', 1)
            if len(filename_parts) == 2:
                clean_name = f"{filename_parts[0]}_clean.{filename_parts[1]}"
            else:
                clean_name = f"{uploaded_file.name}_clean"
            
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
            
            # Redact PII for images and PDFs
            mime = uploaded_file.content_type or ''
            from redaction.utils import is_image_mime, is_pdf_mime
            
            if is_image_mime(mime) or is_pdf_mime(mime):
                from redaction.detector import detect_sensitive_regions
                from redaction.redactor import redact_image
                from redaction.utils import pdf_to_images, images_to_pdf_bytes, image_to_png_bytes
                from PIL import Image
                import io
                from django.core.files.base import ContentFile
                
                try:
                    if hasattr(cleaned_file, 'read'):
                        cleaned_file.seek(0)
                        img_data = cleaned_file.read()
                    else:
                        img_data = cleaned_file
                        
                    if is_pdf_mime(mime):
                        pages = pdf_to_images(img_data)
                        redacted_pages = [redact_image(p, detect_sensitive_regions(p)) for p in pages]
                        cleaned_file = ContentFile(images_to_pdf_bytes(redacted_pages))
                    else:
                        image = Image.open(io.BytesIO(img_data))
                        detections = detect_sensitive_regions(image)
                        if detections:
                            redacted_image = redact_image(image, detections)
                            cleaned_file = ContentFile(image_to_png_bytes(redacted_image))
                except Exception:
                    pass

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
    permission_classes = (AllowAny,)
    
    def get(self, request, share_token):
        from django.utils import timezone
        try:
            file_analysis = FileAnalysis.objects.get(share_token=share_token, is_public=True)
            
            # Expiry Check
            if file_analysis.share_expiry and file_analysis.share_expiry < timezone.now():
                return Response({'error': 'Secure link has expired'}, status=status.HTTP_403_FORBIDDEN)
                
            if not file_analysis.cleaned_file:
                return Response({'error': 'Cleaned file not available'}, status=status.HTTP_404_NOT_FOUND)
                
            response = FileResponse(
                file_analysis.cleaned_file.open('rb'),
                as_attachment=True,
                filename=f"shared_{file_analysis.original_filename}"
            )
            return response
            
        except FileAnalysis.DoesNotExist:
            return Response({'error': 'File not found or private'}, status=status.HTTP_404_NOT_FOUND)
    
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
        
        # Correctly point to the /api/share/ route
        share_url = request.build_absolute_uri(f'/api/share/{file_analysis.share_token}/')
        
        return Response({
            'share_token': str(file_analysis.share_token),
            'share_url': share_url
        }, status=status.HTTP_200_OK)


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


class PipelineProcessView(APIView):
    """
    Unified metadata removal and PII redaction pipeline.
    """
    def post(self, request):
        from pipeline.orchestrator import PipelineOrchestrator
        from main.serializers import FileUploadSerializer
        import tempfile
        import os
        from rest_framework import status
        
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        uploaded_file = serializer.validated_data['file']
        platform = serializer.validated_data.get('platform', 'general')
        apply_signature = request.data.get('apply_signature') == 'true'
        apply_redaction = request.data.get('apply_redaction') == 'true'
        
        # 1. Save uploaded file to a temporary location
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
            
        try:
            # 2. Run the Orchestrator
            orchestrator = PipelineOrchestrator()
            pipeline_result = orchestrator.run(
                file_path=tmp_path,
                platform=platform,
                user_id=request.user.id if request.user.is_authenticated else None,
                apply_signature=apply_signature,
                apply_redaction=apply_redaction
            )

            # 3. Save to FileAnalysis so it can be downloaded/referenced
            from .models import FileAnalysis
            import os
            file_analysis = FileAnalysis.objects.create(
                user=request.user if request.user.is_authenticated else None,
                original_filename=uploaded_file.name,
                file_type=uploaded_file.content_type or 'application/octet-stream',
                file_size=os.path.getsize(pipeline_result.output_file_path),
                platform=platform,
                risk_score=pipeline_result.risk_score,
                status='cleaned'
            )
            
            # Save the processed file to both original and cleaned fields
            with open(pipeline_result.output_file_path, 'rb') as f:
                content = f.read()
                f_name = f"pipeline_{uploaded_file.name}"
                
                # Use ContentFile to save multiple times if needed, or just reopen
                from django.core.files.base import ContentFile
                file_analysis.original_file.save(f_name, ContentFile(content), save=False)
                file_analysis.cleaned_file.save(f_name, ContentFile(content), save=True)

            
            # Return combined data
            response_data = pipeline_result.dict()
            response_data['analysis_id'] = file_analysis.id
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"❌ Pipeline Error: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class BulkPipelineView(APIView):
    """
    Asynchronous bulk file processing using Celery.
    """
    def post(self, request):
        from pipeline.bulk_queue import submit_bulk
        from rest_framework import status
        import tempfile
        import os
        
        files = request.FILES.getlist('files')
        platform = request.data.get('platform', 'general')
        encrypt = request.data.get('encrypt', 'false').lower() == 'true'
        apply_signature = request.data.get('apply_signature') == 'true'
        apply_redaction = request.data.get('apply_redaction') == 'true'
        password = request.data.get('password', None)
        
        if not files:
            return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        files_data = []
        # Ensure project-level temp directory exists
        bulk_temp = os.path.join(settings.BASE_DIR, 'bulk_temp')
        os.makedirs(bulk_temp, exist_ok=True)

        for i, uploaded_file in enumerate(files):
            # Create a truly unique filename using index and timestamp
            unique_name = f"{int(time.time())}_{i}_{uploaded_file.name}"
            tmp_path = os.path.join(bulk_temp, unique_name)
            
            with open(tmp_path, 'wb+') as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
            
            files_data.append((tmp_path, uploaded_file.name))
        
        try:
            user_id = request.user.id if request.user.is_authenticated else None
            job_id = submit_bulk(files_data, platform, encrypt, password, user_id, apply_signature=apply_signature, apply_redaction=apply_redaction)
            print(f"🚀 Bulk Job Submitted: {job_id} ({len(files)} files)")
            return Response({
                "message": f"Bulk job submitted successfully: {len(files)} files",
                "job_id": job_id,
                "status": "processing"
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BulkZipDownloadView(APIView):
    """
    Download all files in a bulk job as a single ZIP file.
    """
    def get(self, request, job_id):
        from .models import FileAnalysis
        import zipfile
        import io
        from django.utils import timezone
        import datetime
        
        print(f"📦 Generating ZIP for Job ID: {job_id}")
        
        # 1. Try to find by Job ID
        records = FileAnalysis.objects.filter(job_id=job_id, status='cleaned')
        
        # 2. Fallback: If no job_id found, get recent files for this user (if logged in)
        if not records.exists() and request.user.is_authenticated:
            print("⚠️ No records found by Job ID, trying fallback to recent files...")
            records = FileAnalysis.objects.filter(
                user=request.user, 
                status='cleaned',
                created_at__gte=timezone.now() - datetime.timedelta(minutes=10)
            )[:10]
            
        if not records.exists():
            print("❌ No files found to ZIP!")
            return Response({"error": "No cleaned files found for this job"}, status=status.HTTP_404_NOT_FOUND)
            
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_obj in records:
                if file_obj.cleaned_file:
                    try:
                        # Use absolute path to ensure we can read it
                        path = file_obj.cleaned_file.path
                        with open(path, 'rb') as f:
                            content = f.read()
                            if content:
                                arc_name = f"clean_{file_obj.original_filename}"
                                zip_file.writestr(arc_name, content)
                                print(f"✅ Added to ZIP: {arc_name}")
                    except Exception as e:
                        print(f"⚠️ Failed to add {file_obj.id}: {e}")
        
        zip_buffer.seek(0)
        response = FileResponse(
            zip_buffer,
            as_attachment=True,
            filename=f"bulk_processed_{job_id[:8] if job_id else 'batch'}.zip"
        )
        response['Content-Type'] = 'application/zip'
        return response

class BulkJobStatusView(APIView):
    """
    Check the status of a bulk processing job.
    """
    def get(self, request, job_id):
        from pipeline.bulk_queue import get_bulk_status
        print(f"📡 API Request: Bulk Status for {job_id}")
        status_data = get_bulk_status(job_id)
        return Response(status_data)
# ============================================================
# SECURE SHARE MODULE
# ============================================================
from django.utils import timezone
from .models import SecureShare, SecureShareAccessLog
from .serializers import (
    SecureShareCreateSerializer,
    SecureShareInfoSerializer,
    SecureShareAccessLogSerializer,
)
from django.http import HttpResponse


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class SecureShareCreateView(generics.CreateAPIView):
    """
    POST /api/secure-share/create/
    Body: { file_analysis_id, password?, expires_at?, max_downloads?, is_one_time? }
    Returns: { token, share_url, message }
    """
    serializer_class = SecureShareCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        share = serializer.save()

        base_url = getattr(settings, 'PUBLIC_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
        share_url = f"{base_url}/secure-share/{share.token}/"

        return Response({
            'token': str(share.token),
            'share_url': share_url,
            'message': 'Secure share created successfully',
        }, status=status.HTTP_201_CREATED)


class SecureShareInfoView(APIView):
    """
    GET /api/secure-share/<token>/info/
    Public endpoint — returns metadata about the share (no file content).
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            share = SecureShare.objects.get(token=token)
        except SecureShare.DoesNotExist:
            return Response({'error': 'Share not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SecureShareInfoSerializer(share)
        return Response(serializer.data)


class SecureShareDownloadView(APIView):
    """
    POST /api/secure-share/<token>/download/
    Body: { password? }
    Downloads the cleaned file if the share is valid and auth passes.
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            share = SecureShare.objects.get(token=token)
        except SecureShare.DoesNotExist:
            return Response({'error': 'Share not found'}, status=status.HTTP_404_NOT_FOUND)

        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')

        if not share.is_valid():
            SecureShareAccessLog.objects.create(
                share=share, ip_address=ip, user_agent=ua,
                action='download', success=False,
                error_message='Link expired or inactive',
            )
            return Response({'error': 'Link is no longer valid'}, status=status.HTTP_403_FORBIDDEN)

        password = request.data.get('password', '')
        if share.password_hash and not share.check_password(password):
            SecureShareAccessLog.objects.create(
                share=share, ip_address=ip, user_agent=ua,
                action='failed_auth', success=False,
                error_message='Invalid password',
            )
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Log success & increment counter
        SecureShareAccessLog.objects.create(
            share=share, ip_address=ip, user_agent=ua,
            action='download', success=True,
        )
        share.current_downloads += 1
        share.save(update_fields=['current_downloads'])

        file_analysis = share.file_analysis
        
        if not file_analysis.cleaned_file:
            return Response({'error': 'Cleaned file not available'}, status=status.HTTP_404_NOT_FOUND)

        file_size = file_analysis.cleaned_file.size
        safe_name = f"secure_{file_analysis.original_filename}"

        if file_size > 10 * 1024 * 1024:
            response = StreamingHttpResponse(
                file_iterator(file_analysis.cleaned_file.open('rb')),
                content_type=file_analysis.file_type,
            )
            response['Content-Disposition'] = f'attachment; filename="{safe_name}"'
            response['Content-Length'] = file_size
        else:
            response = FileResponse(
                file_analysis.cleaned_file.open('rb'),
                as_attachment=True,
                filename=safe_name,
            )
            response['Content-Length'] = file_size
        return response


class SecureShareRevokeView(APIView):
    """
    POST /api/secure-share/<token>/revoke/
    Deactivates the share link immediately.
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            share = SecureShare.objects.get(token=token)
        except SecureShare.DoesNotExist:
            return Response({'error': 'Share not found'}, status=status.HTTP_404_NOT_FOUND)

        share.is_active = False
        share.save(update_fields=['is_active'])
        return Response({'message': 'Share revoked successfully'})


class SecureShareLogsView(generics.ListAPIView):
    """
    GET /api/secure-share/<token>/logs/
    Returns the access log for a share token.
    """
    serializer_class = SecureShareAccessLogSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SecureShareAccessLog.objects.filter(share__token=self.kwargs['token'])


class SecureSharePageView(APIView):
    """
    GET /secure-share/<token>/
    Public HTML receiver page served directly from Django.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Secure File Download</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f0f4f8 0%, #e8edf2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.08);
            padding: 40px 36px;
            width: 100%;
            max-width: 460px;
            text-align: center;
        }}
        .shield {{
            width: 56px; height: 56px;
            background: linear-gradient(135deg, #4dabf7, #339af0);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 20px;
        }}
        .shield svg {{ stroke: #fff; }}
        h1 {{ color: #1a202c; font-size: 22px; margin-bottom: 6px; }}
        .subtitle {{ color: #718096; font-size: 14px; margin-bottom: 28px; }}
        .info-box {{
            background: #f7fafc; border: 1px solid #e2e8f0;
            border-radius: 10px; padding: 16px; margin-bottom: 24px; text-align: left;
        }}
        .info-row {{ display: flex; justify-content: space-between; padding: 6px 0; font-size: 14px; }}
        .info-row span:first-child {{ color: #718096; }}
        .info-row span:last-child {{ color: #2d3748; font-weight: 600; }}
        .badge {{
            display: inline-block; padding: 2px 8px; border-radius: 99px;
            font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
        }}
        .badge-active {{ background: #c6f6d5; color: #276749; }}
        .badge-inactive {{ background: #fed7d7; color: #9b2c2c; }}
        label {{ display: block; text-align: left; font-size: 13px; font-weight: 600; color: #4a5568; margin-bottom: 6px; }}
        input[type="password"] {{
            width: 100%; padding: 12px 14px; border: 1.5px solid #e2e8f0;
            border-radius: 8px; font-size: 14px; outline: none; transition: border-color .2s;
            margin-bottom: 20px;
        }}
        input[type="password"]:focus {{ border-color: #4dabf7; box-shadow: 0 0 0 3px rgba(77,171,247,.15); }}
        .btn {{
            display: block; width: 100%; padding: 13px;
            border: none; border-radius: 8px; font-size: 16px;
            font-weight: 700; cursor: pointer; transition: all .2s;
        }}
        .btn-primary {{ background: linear-gradient(135deg, #4dabf7, #339af0); color: #fff; }}
        .btn-primary:hover:not(:disabled) {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(51,154,240,.4); }}
        .btn:disabled {{ opacity: .6; cursor: not-allowed; }}
        .error {{ color: #e53e3e; font-size: 13px; margin-top: 14px; display: none; }}
        .spinner {{
            width: 40px; height: 40px; border: 3px solid #e2e8f0;
            border-top-color: #4dabf7; border-radius: 50%;
            animation: spin .8s linear infinite; margin: 0 auto 16px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .loading-text {{ color: #718096; font-size: 14px; }}
    </style>
</head>
<body>
<div class="card">
    <div class="shield">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L3 7V12C3 16.55 6.84 20.74 12 22C17.16 20.74 21 16.55 21 12V7L12 2Z"/>
            <path d="M9 12L11 14L15 10"/>
        </svg>
    </div>
    <h1>Secure File Download</h1>
    <p class="subtitle">This file was shared securely with metadata removed.</p>

    <div id="loading">
        <div class="spinner"></div>
        <p class="loading-text">Fetching file details&hellip;</p>
    </div>

    <div id="main" style="display:none">
        <div class="info-box" id="infoBox"></div>
        <div id="pwSection" style="display:none">
            <label for="pw">Share Password</label>
            <input type="password" id="pw" placeholder="Enter password to unlock">
        </div>
        <button class="btn btn-primary" id="dlBtn" onclick="doDownload()">Download File</button>
        <div class="error" id="errMsg"></div>
    </div>
</div>

<script>
const TOKEN = '{token}';
let needsPassword = false;

(async () => {{
    try {{
        const res = await fetch(`/api/secure-share/${{TOKEN}}/info/`);
        const data = await res.json();
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main').style.display = 'block';

        if (data.error || !data.is_valid) {{
            document.getElementById('infoBox').innerHTML =
                '<div style="color:#e53e3e;text-align:center;padding:8px">' +
                (data.error || 'This link is no longer valid or has expired.') + '</div>';
            document.getElementById('dlBtn').disabled = true;
            return;
        }}

        const sizeMB = (data.file_size / (1024 * 1024)).toFixed(2);
        const badge = data.is_valid
            ? '<span class="badge badge-active">Active</span>'
            : '<span class="badge badge-inactive">Expired</span>';

        document.getElementById('infoBox').innerHTML = `
            <div class="info-row"><span>File</span><span>${{data.filename}}</span></div>
            <div class="info-row"><span>Size</span><span>${{sizeMB}} MB</span></div>
            <div class="info-row"><span>Downloads</span><span>${{data.current_downloads}} / ${{data.max_downloads || '&infin;'}}</span></div>
            <div class="info-row"><span>Status</span><span>${{badge}}</span></div>
        `;

        needsPassword = data.has_password;
        if (needsPassword) document.getElementById('pwSection').style.display = 'block';
    }} catch (e) {{
        document.getElementById('loading').innerHTML =
            '<p style="color:#e53e3e">Error connecting to server.</p>';
    }}
}})();

function showErr(msg) {{
    const el = document.getElementById('errMsg');
    el.textContent = msg;
    el.style.display = 'block';
}}

async function doDownload() {{
    document.getElementById('errMsg').style.display = 'none';
    const pw = document.getElementById('pw')?.value || '';

    if (needsPassword && !pw) {{ showErr('Password is required.'); return; }}

    const btn = document.getElementById('dlBtn');
    btn.textContent = 'Downloading\u2026'; btn.disabled = true;

    try {{
        const res = await fetch(`/api/secure-share/${{TOKEN}}/download/`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ password: pw }}),
        }});

        if (!res.ok) {{
            const d = await res.json().catch(() => ({{}}));
            throw new Error(d.error || 'Download failed');
        }}

        const disposition = res.headers.get('Content-Disposition') || '';
        let filename = 'secure_file';
        const m = /filename="([^"]+)"/.exec(disposition);
        if (m) filename = m[1];

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        btn.textContent = 'Downloaded \u2713'; btn.disabled = false;
    }} catch (e) {{
        showErr(e.message);
        btn.textContent = 'Download File'; btn.disabled = false;
    }}
}}
</script>
</body>
</html>'''
        return HttpResponse(html, content_type='text/html')
