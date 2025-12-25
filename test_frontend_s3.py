"""
Quick S3 Template Integration Test for Frontend
Tests all endpoints that the frontend uses
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("S3 TEMPLATE INTEGRATION - FRONTEND TEST")
print("=" * 70)
print()

# Test 1: Get Template Info
print("Test 1: Get Template Information")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/v1/crs-documents/documents/template-info/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS")
        print(f"   Template: {data.get('template', {}).get('key')}")
        print(f"   Size: {data.get('template', {}).get('size')} bytes")
        print(f"   Bucket: {data.get('template', {}).get('bucket')}")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print()

# Test 2: Download Template
print("Test 2: Download Template File")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/v1/crs-documents/documents/download-template/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        content_length = len(response.content)
        print(f"✅ SUCCESS")
        print(f"   Downloaded: {content_length} bytes")
        print(f"   Type: {content_type}")
        
        # Save to test file
        with open("test_downloaded_template.xlsx", "wb") as f:
            f.write(response.content)
        print(f"   Saved as: test_downloaded_template.xlsx")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print()

# Test 3: Validate Template
print("Test 3: Validate Template")
print("-" * 70)
try:
    with open("test_downloaded_template.xlsx", "rb") as f:
        files = {'template_file': f}
        response = requests.post(
            f"{BASE_URL}/api/v1/crs-documents/documents/validate-template/",
            files=files
        )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS")
        print(f"   Valid: {data.get('valid')}")
        print(f"   Sheet: {data.get('sheet_name')}")
        print(f"   Rows: {data.get('row_count')}")
        print(f"   Columns: {data.get('column_count')}")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print()
print("Frontend can access these endpoints:")
print(f"  → {BASE_URL}/api/v1/crs-documents/documents/template-info/")
print(f"  → {BASE_URL}/api/v1/crs-documents/documents/download-template/")
print(f"  → {BASE_URL}/api/v1/crs-documents/documents/validate-template/")
print()
