class DisableCSRFForAPI:
    """
    Middleware to disable CSRF protection for API endpoints.
    This is safe because we use Token Authentication for API requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Disable CSRF for all /api/ endpoints
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)