from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FileAnalysisViewSet,
    AnalyzeFileView,
    CleanFileView,
    CleanAndDownloadView,
    ShareFileView,
    MakePublicView,
    PlatformRuleViewSet,
    HealthCheckView
)

router = DefaultRouter()
router.register(r'analyses', FileAnalysisViewSet, basename='fileanalysis')
router.register(r'platform-rules', PlatformRuleViewSet, basename='platformrule')

urlpatterns = [
    path('', include(router.urls)),
    path('analyze/', AnalyzeFileView.as_view(), name='analyze-file'),
    path('clean/', CleanFileView.as_view(), name='clean-file'),
    path('clean-download/', CleanAndDownloadView.as_view(), name='clean-download'),
    path('share/<uuid:share_token>/', ShareFileView.as_view(), name='share-file'),
    path('make-public/<uuid:pk>/', MakePublicView.as_view(), name='make-public'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]