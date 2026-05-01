from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main.views import SecureSharePageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('api/redact/', include('redaction.urls')),
    # Public receiver page — outside /api/ so share links work without auth
    path('secure-share/<uuid:token>/', SecureSharePageView.as_view(), name='secure-share-page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)