from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DecryptFileView,
    EncryptFileView,
    FileAnalysisViewSet,
    AnalyzeFileView,
    CleanFileView,
    CleanAndDownloadView,
    GoogleLoginTokenView,
    ShareFileView,
    MakePublicView,
    PlatformRuleViewSet,
    HealthCheckView,
    ValidatePasswordView,
    RegisterView, LoginView, LogoutView, UserProfileView,
    UpdateProfileView, ChangePasswordView, DeleteAccountView,GoogleCallbackView, GoogleLoginView
)


router = DefaultRouter()
router.register(r'analyses', FileAnalysisViewSet, basename='fileanalysis')
router.register(r'platform-rules', PlatformRuleViewSet, basename='platformrule')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/profile/', UserProfileView.as_view(), name='auth-profile'),
    path('auth/profile/update/', UpdateProfileView.as_view(), name='auth-profile-update'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='auth-delete-account'),
    path('api/auth/google/login/', GoogleLoginView.as_view(), name='google-login'),
    path('api/auth/google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
    path('api/auth/google/verify/', GoogleLoginTokenView.as_view(), name='google-verify'),
    
    path('analyze/', AnalyzeFileView.as_view(), name='analyze-file'),
    path('clean/', CleanFileView.as_view(), name='clean-file'),
    path('clean-download/', CleanAndDownloadView.as_view(), name='clean-download'),
    path('share/<uuid:share_token>/', ShareFileView.as_view(), name='share-file'),
    path('make-public/<uuid:pk>/', MakePublicView.as_view(), name='make-public'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('encrypt/', EncryptFileView.as_view(), name='encrypt-file'),
    path('decrypt/', DecryptFileView.as_view(), name='decrypt-file'),
    path('validate-password/', ValidatePasswordView.as_view(), name='validate-password'),
    
]