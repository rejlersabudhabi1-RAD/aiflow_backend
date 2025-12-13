"""
AWS S3 Storage Backends
Secure S3 storage configuration using django-storages
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    S3 storage backend for media files (P&ID drawings, reports, avatars)
    
    Security features:
    - Uses environment variables for configuration
    - No hardcoded credentials
    - Supports IAM roles (EC2/ECS/Lambda)
    - Custom expiration for presigned URLs
    """
    
    location = 'media'
    default_acl = None  # Disable ACLs (use bucket policy instead)
    file_overwrite = False   # Don't overwrite files with same name
    custom_domain = False    # Use presigned URLs instead of public URLs
    
    # Security: Use temporary presigned URLs (expires in 1 hour)
    querystring_expire = 3600  # 1 hour
    
    # Performance optimizations
    object_parameters = {
        'CacheControl': 'max-age=86400',  # 24 hours
    }


class StaticStorage(S3Boto3Storage):
    """
    S3 storage backend for static files (CSS, JS, images)
    
    Static files can be public since they don't contain sensitive data
    """
    
    location = 'static'
    default_acl = None  # Disable ACLs (use bucket policy for public access)
    file_overwrite = True         # Overwrite on deployment
    
    # Cache static files for 1 year (immutable)
    object_parameters = {
        'CacheControl': 'max-age=31536000, immutable',
    }


class PIDDrawingStorage(S3Boto3Storage):
    """
    Dedicated S3 storage for P&ID drawings
    
    Features:
    - Isolated folder structure
    - Private access only
    - Long-term storage (no automatic deletion)
    - Presigned URLs for secure downloads
    """
    
    location = 'media/pid_drawings'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
    querystring_expire = 7200  # 2 hours (longer for analysis processing)
    
    # Metadata for tracking
    object_parameters = {
        'CacheControl': 'max-age=86400',
        'Metadata': {
            'app': 'aiflow',
            'content_type': 'pid_drawing'
        }
    }


class PIDReportStorage(S3Boto3Storage):
    """
    Dedicated S3 storage for generated P&ID reports (PDF, Excel)
    
    Features:
    - Isolated folder structure
    - Private access only
    - Presigned URLs for downloads
    """
    
    location = 'media/pid_reports'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
    querystring_expire = 3600  # 1 hour
    
    object_parameters = {
        'CacheControl': 'max-age=86400',
        'Metadata': {
            'app': 'aiflow',
            'content_type': 'pid_report'
        }
    }
