"""
redaction/urls.py
-----------------
URL routes owned entirely by the redaction module.

These are included in the main url conf with ONE line (see integration
instructions below).  No existing urls.py is modified.

Integration (add to  automated/urls.py):
-----------------------------------------
    from django.urls import path, include          # already present

    urlpatterns = [
        ...                                        # existing entries untouched
        path('api/redact/', include('redaction.urls')),   # ← ADD THIS LINE
    ]
"""

from django.urls import path
from .views import RedactView

app_name = "redaction"

urlpatterns = [
    # POST /api/redact/
    path("", RedactView.as_view(), name="redact"),
]
