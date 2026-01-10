from django.urls import path
from . import views

app_name = 'metadata'

urlpatterns = [
    # Main endpoints
    path('analyze/', views.MetadataAnalysisView.as_view(), name='analyze'),
    path('remove/', views.MetadataRemovalView.as_view(), name='remove'),
    path('batch-remove/', views.BatchMetadataRemovalView.as_view(), name='batch-remove'),
    
    # Platform rules
    path('platforms/', views.PlatformRulesView.as_view(), name='platforms'),
    
    # Utility endpoints
    path('health/', views.health_check, name='health'),
    path('formats/', views.supported_formats, name='formats'),
]
