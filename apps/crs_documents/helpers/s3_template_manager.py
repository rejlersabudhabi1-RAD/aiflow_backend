"""
S3 Template Manager for CRS Documents
Downloads and caches the CRS template from S3
"""

import boto3
from io import BytesIO
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# S3 Configuration
S3_BUCKET = 'user-management-rejlers'
S3_REGION = 'ap-south-1'
S3_TEMPLATE_KEY = 'CRS template.xlsx'  # Actual filename (boto3 handles URL encoding)
TEMPLATE_CACHE_KEY = 'crs_template_xlsx'
CACHE_TIMEOUT = 3600 * 24  # Cache for 24 hours


def get_s3_client():
    """
    Get configured S3 client with credentials from settings
    """
    try:
        # Get credentials from Django settings (loaded from .env)
        aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        
        if not aws_access_key or not aws_secret_key:
            logger.error("AWS credentials not found in settings. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
            return None
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=S3_REGION
        )
        
        return s3_client
    
    except Exception as e:
        logger.error(f"Error creating S3 client: {str(e)}")
        return None


def download_crs_template_from_s3(use_cache=True):
    """
    Download CRS template from S3 bucket
    
    Args:
        use_cache: If True, try to get from cache first
    
    Returns:
        BytesIO: Template file buffer or None if failed
    """
    try:
        # Try cache first
        if use_cache:
            cached_template = cache.get(TEMPLATE_CACHE_KEY)
            if cached_template:
                logger.info("Retrieved CRS template from cache")
                return BytesIO(cached_template)
        
        # Download from S3
        logger.info(f"Downloading CRS template from S3: {S3_BUCKET}/{S3_TEMPLATE_KEY}")
        s3_client = get_s3_client()
        
        if not s3_client:
            logger.error("Failed to create S3 client")
            return None
        
        # Download file
        template_buffer = BytesIO()
        s3_client.download_fileobj(S3_BUCKET, S3_TEMPLATE_KEY, template_buffer)
        template_buffer.seek(0)
        
        # Cache the template
        if use_cache:
            cache.set(TEMPLATE_CACHE_KEY, template_buffer.getvalue(), CACHE_TIMEOUT)
            logger.info("Cached CRS template for future use")
        
        logger.info(f"Successfully downloaded CRS template ({len(template_buffer.getvalue())} bytes)")
        return template_buffer
    
    except Exception as e:
        logger.error(f"Error downloading CRS template from S3: {str(e)}")
        return None


def get_crs_template():
    """
    Get CRS template - tries multiple sources in order:
    1. S3 bucket (primary source)
    2. Local fallback file (if exists)
    
    Returns:
        BytesIO: Template file buffer or None if all sources fail
    """
    # Try S3 first
    template_buffer = download_crs_template_from_s3(use_cache=True)
    
    if template_buffer:
        return template_buffer
    
    # Fallback to local file if S3 fails
    logger.warning("S3 download failed, checking for local fallback template")
    
    import os
    local_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'test', 'crs', 'CRS template.xlsx'
    )
    
    if os.path.exists(local_template_path):
        logger.info(f"Using local fallback template: {local_template_path}")
        with open(local_template_path, 'rb') as f:
            return BytesIO(f.read())
    
    logger.error("No CRS template available from S3 or local file")
    return None


def refresh_template_cache():
    """
    Force refresh the cached template from S3
    Useful when template is updated
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    try:
        cache.delete(TEMPLATE_CACHE_KEY)
        logger.info("Cleared template cache")
        
        template = download_crs_template_from_s3(use_cache=True)
        return template is not None
    
    except Exception as e:
        logger.error(f"Error refreshing template cache: {str(e)}")
        return False


def upload_template_to_s3(template_buffer: BytesIO, filename: str = None):
    """
    Upload a new CRS template to S3
    Requires appropriate S3 permissions
    
    Args:
        template_buffer: BytesIO containing template file
        filename: Optional custom filename (defaults to CRS+template.xlsx)
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        
        if not s3_client:
            logger.error("Failed to create S3 client for upload")
            return False
        
        key = filename if filename else S3_TEMPLATE_KEY
        
        template_buffer.seek(0)
        s3_client.upload_fileobj(
            template_buffer,
            S3_BUCKET,
            key,
            ExtraArgs={'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
        )
        
        # Refresh cache with new template
        cache.delete(TEMPLATE_CACHE_KEY)
        
        logger.info(f"Successfully uploaded template to S3: {S3_BUCKET}/{key}")
        return True
    
    except Exception as e:
        logger.error(f"Error uploading template to S3: {str(e)}")
        return False


def get_template_metadata():
    """
    Get metadata about the CRS template from S3
    
    Returns:
        dict: Metadata including size, last modified, etc.
    """
    try:
        s3_client = get_s3_client()
        
        if not s3_client:
            return {'error': 'Failed to create S3 client'}
        
        response = s3_client.head_object(Bucket=S3_BUCKET, Key=S3_TEMPLATE_KEY)
        
        return {
            'size': response.get('ContentLength'),
            'last_modified': response.get('LastModified'),
            'content_type': response.get('ContentType'),
            'etag': response.get('ETag'),
            'bucket': S3_BUCKET,
            'key': S3_TEMPLATE_KEY,
            'region': S3_REGION,
        }
    
    except Exception as e:
        logger.error(f"Error getting template metadata: {str(e)}")
        return {'error': str(e)}
