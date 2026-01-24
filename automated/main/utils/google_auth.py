from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
import requests as http_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from main.serializers import UserSerializer



class GoogleOAuth:
    """Handle Google OAuth authentication"""
    
    @staticmethod
    def get_google_auth_url():
        """Generate Google OAuth URL for user login"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        from urllib.parse import urlencode
        return f"{base_url}?{urlencode(params)}"
    
    @staticmethod
    def exchange_code_for_token(code):
        """Exchange authorization code for access token"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        response = http_requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")
        
        return response.json()
    
    @staticmethod
    def get_user_info(access_token):
        """Get user information from Google"""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = http_requests.get(userinfo_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get user info: {response.text}")
        
        return response.json()
    
    @staticmethod
    def verify_google_token(token):
        """Verify Google ID token"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return idinfo
        except Exception as e:
            raise Exception(f"Token verification failed: {str(e)}")


