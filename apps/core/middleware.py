"""
Custom Middleware for AIFlow
Ensures CORS headers are always present
"""
from django.http import HttpResponse


class CorsMiddleware:
    """
    Custom CORS middleware to ensure headers are always added
    This is a fallback to ensure CORS works even if django-cors-headers fails
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # List of allowed origins
        allowed_origins = [
            'https://airflow-frontend.vercel.app',
            'http://localhost:3000',
            'http://localhost:5173',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
        ]
        
        # Check if origin is allowed (exact match or Vercel domain)
        is_allowed = (
            origin in allowed_origins or 
            origin.endswith('.vercel.app') or
            'localhost' in origin or
            '127.0.0.1' in origin
        )
        
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS' and is_allowed:
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Accept, Accept-Encoding, Authorization, Content-Type, DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With'
            response['Access-Control-Max-Age'] = '86400'
            return response
        
        # Process the request
        response = self.get_response(request)
        
        # Add CORS headers to response
        if is_allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Accept, Accept-Encoding, Authorization, Content-Type, DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With'
            response['Access-Control-Max-Age'] = '86400'
        
        return response
