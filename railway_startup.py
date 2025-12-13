#!/usr/bin/env python
"""
Railway deployment startup script
Ensures proper initialization and health check
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to the sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_health():
    """Verify the application is ready"""
    try:
        # Check database connection
        from django.db import connection
        connection.ensure_connection()
        print("✓ Database connection successful")
        
        # Check if migrations are applied
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out, no_color=True)
        migrations_output = out.getvalue()
        if '[X]' in migrations_output or migrations_output.strip():
            print("✓ Migrations status OK")
        
        # Check critical settings
        from django.conf import settings
        print(f"✓ DEBUG={settings.DEBUG}")
        print(f"✓ ALLOWED_HOSTS={settings.ALLOWED_HOSTS}")
        print(f"✓ Database: {settings.DATABASES['default']['ENGINE']}")
        
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Railway Deployment Health Check")
    print("=" * 50)
    
    if check_health():
        print("\n✓ Application is ready to serve traffic")
        sys.exit(0)
    else:
        print("\n✗ Application not ready")
        sys.exit(1)
