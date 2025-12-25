"""
Test script for CRS Documents S3 Template Integration
Tests all new endpoints and functionality
"""

import requests
import json
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/crs-documents/documents"

# Test results
results = []

def test_result(name, success, message="", data=None):
    """Store test result"""
    results.append({
        'test': name,
        'success': success,
        'message': message,
        'data': data
    })
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"      {message}")
    if data:
        print(f"      Data: {json.dumps(data, indent=6, default=str)}")
    print()

def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r['success']:
                print(f"   - {r['test']}: {r['message']}")
    
    print("\n" + "="*70)

def main():
    print("="*70)
    print("CRS DOCUMENTS - S3 TEMPLATE INTEGRATION TESTS")
    print("="*70)
    print()

    # Test 1: Template Info
    print("Test 1: Get Template Information from S3")
    print("-" * 70)
    try:
        response = requests.get(f"{API_BASE}/template-info/")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                template_info = data.get('template', {})
                test_result(
                    "Get Template Info",
                    True,
                    f"Template size: {template_info.get('size')} bytes",
                    template_info
                )
            else:
                test_result("Get Template Info", False, "API returned success=False")
        else:
            test_result("Get Template Info", False, f"HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        test_result("Get Template Info", False, f"Exception: {str(e)}")

    # Test 2: Download Template
    print("Test 2: Download Template from S3")
    print("-" * 70)
    try:
        response = requests.get(f"{API_BASE}/download-template/")
        if response.status_code == 200:
            content_length = len(response.content)
            content_type = response.headers.get('Content-Type', '')
            test_result(
                "Download Template",
                True,
                f"Downloaded {content_length} bytes, Type: {content_type}",
                {'size': content_length, 'content_type': content_type}
            )
        else:
            test_result("Download Template", False, f"HTTP {response.status_code}")
    except Exception as e:
        test_result("Download Template", False, f"Exception: {str(e)}")

    # Test 3: Validate Template (using downloaded template)
    print("Test 3: Validate Template Format")
    print("-" * 70)
    try:
        # First download the template
        response = requests.get(f"{API_BASE}/download-template/")
        if response.status_code == 200:
            # Now validate it
            files = {'template_file': ('template.xlsx', BytesIO(response.content))}
            validate_response = requests.post(f"{API_BASE}/validate-template/", files=files)
            
            if validate_response.status_code == 200:
                data = validate_response.json()
                test_result(
                    "Validate Template",
                    data.get('valid', False),
                    data.get('message', 'Template validated'),
                    data
                )
            else:
                test_result("Validate Template", False, f"HTTP {validate_response.status_code}")
        else:
            test_result("Validate Template", False, "Could not download template for validation")
    except Exception as e:
        test_result("Validate Template", False, f"Exception: {str(e)}")

    # Test 4: Cache Refresh
    print("Test 4: Refresh Template Cache")
    print("-" * 70)
    try:
        response = requests.post(f"{API_BASE}/refresh-template-cache/")
        if response.status_code == 200:
            data = response.json()
            test_result(
                "Refresh Template Cache",
                data.get('success', False),
                data.get('message', ''),
                data
            )
        else:
            test_result("Refresh Template Cache", False, f"HTTP {response.status_code}")
    except Exception as e:
        test_result("Refresh Template Cache", False, f"Exception: {str(e)}")

    # Test 5: Backend Health Check
    print("Test 5: Backend API Health Check")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/")
        if response.status_code == 200:
            test_result("Backend Health", True, "Backend is healthy")
        else:
            test_result("Backend Health", False, f"HTTP {response.status_code}")
    except Exception as e:
        test_result("Backend Health", False, f"Exception: {str(e)}")

    # Print summary
    print_summary()

    # Additional Information
    print("\n" + "="*70)
    print("ADDITIONAL INFORMATION")
    print("="*70)
    print("\n📚 Available Endpoints:")
    print(f"   • GET  {API_BASE}/template-info/")
    print(f"   • GET  {API_BASE}/download-template/")
    print(f"   • POST {API_BASE}/validate-template/")
    print(f"   • POST {API_BASE}/refresh-template-cache/")
    print(f"   • POST {API_BASE}/{{id}}/process-pdf-comments/")
    print(f"   • POST {API_BASE}/{{id}}/extract-comments-only/")
    
    print("\n📖 Documentation:")
    print("   See: aiflow_backend/apps/crs_documents/S3_TEMPLATE_INTEGRATION.md")
    
    print("\n🧪 To Test PDF Processing:")
    print("   1. Create a CRS document: POST /api/v1/crs-documents/documents/")
    print("   2. Upload PDF with comments: POST /api/v1/crs-documents/documents/{id}/process-pdf-comments/")
    print("   3. System will use S3 template automatically")
    print()

if __name__ == "__main__":
    main()
