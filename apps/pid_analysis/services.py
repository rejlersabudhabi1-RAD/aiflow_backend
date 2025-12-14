"""
P&ID Analysis Service
AI-powered P&ID verification using OpenAI GPT-4 Vision
"""
import os
import base64
import io
from datetime import datetime
from typing import Dict, List, Any
from django.conf import settings
from openai import OpenAI
import fitz  # PyMuPDF
from PIL import Image


class PIDAnalysisService:
    """Service for analyzing P&ID drawings using OpenAI"""
    
    # Complete P&ID analysis prompt
    ANALYSIS_PROMPT = """🔹 ROLE & CONTEXT

You are an AI-Powered P&ID Design Verification Engine acting as a Senior Process Engineer + Piping Engineer + Instrumentation Engineer with expertise in:

- Oil & Gas P&ID standards
- ADNOC / DEP / API / ISA / ISO practices
- Compressor packages, suction drums, flare systems, chemical injection, antisurge systems
- Engineering review, HAZOP readiness, and design compliance

Your task is to analyze P&ID drawings and identify design errors, inconsistencies, and non-compliances, then generate a formal engineering review report.

🔹 SCOPE OF VERIFICATION

Perform multi-disciplinary checks, including but not limited to:

1️⃣ Equipment Verification
- Vessel dimensions (Height, Diameter)
- Design pressure & temperature
- Minimum / maximum design temperature
- Equipment tag consistency
- Equipment description vs datasheet values

2️⃣ Instrumentation & Control
- Correct instrument tags (LIT, TIT, PIT, PSV, SDV, MOV, LCV, etc.)
- Alarm and trip set points (HH, H, L, LL)
- Fail-safe positions (FC / FO / FL)
- Consistency with Alarm & Trip Schedule
- Correct instrument symbols as per legend

3️⃣ Valve & Safety Systems
- PSV inlet/outlet isolation philosophy (ILO / ILC)
- SDV fail positions clearly marked
- Correct valve type usage (Gate vs Ball vs Control)
- Locking philosophy compliance

4️⃣ Piping & Layout
- Line number correctness
- Slope direction consistency
- Drain and vent routing
- No pockets upstream of NRVs
- Straight run requirements
- Correct connection to flare / closed drain headers

5️⃣ Notes, Legends & Project Rules
- Compliance with project notes
- Type references (Type 01A, 02A, 07B, etc.)
- Missing or conflicting notes
- HOLD items clearly flagged

🔹 ERROR IDENTIFICATION RULES

For each issue found, you must:
- Detect what is wrong
- Explain why it is wrong
- Propose a clear corrective action
- Reference the exact P&ID element/tag

🔹 OUTPUT FORMAT (MANDATORY - JSON)

Return ONLY a valid JSON object with this EXACT structure:

{
  "drawing_info": {
    "drawing_number": "extracted P&ID number",
    "drawing_title": "extracted title",
    "revision": "extracted revision",
    "analysis_date": "current date in ISO format"
  },
  "summary": {
    "total_issues": 0,
    "critical_count": 0,
    "major_count": 0,
    "minor_count": 0,
    "observation_count": 0
  },
  "issues": [
    {
      "serial_number": 1,
      "pid_reference": "V-3610-01 equipment box",
      "category": "Equipment Verification",
      "severity": "major",
      "issue_observed": "V-3610-01 dimensions in equipment box show HEIGHT = 6000 mm (T/T). Correct height as per equipment datasheet is 4000 mm.",
      "action_required": "Revise equipment box to show HEIGHT = 4000 mm (T/T) as per approved datasheet.",
      "approval": "Pending",
      "remark": "Pending",
      "status": "pending"
    }
  ]
}

🔹 ISSUE WRITING GUIDELINES
- Use clear, professional, third-person engineering language
- Do NOT assume approvals - Default status = Pending
- Keep observations concise but technically complete
- Always reference specific tags, line numbers, or equipment

🔹 SEVERITY CLASSIFICATION
- **critical**: Safety-critical issues (PSV, Emergency shutdown, Fire protection)
- **major**: Functional/operational issues (Wrong instrument ranges, valve types)
- **minor**: Documentation issues (Missing notes, legend discrepancies)
- **observation**: Recommendations for improvement

🔹 IMPORTANT CONSTRAINTS
- Do NOT modify the drawing
- Do NOT assume missing data — flag it
- Do NOT invent values
- Always stay within engineering review responsibility
- Output must be ready to forward to Process Engineer

Now analyze the provided P&ID drawing and return ONLY the JSON response."""

    def __init__(self):
        """Initialize OpenAI client"""
        api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=api_key)
    
    def pdf_to_images(self, pdf_file, dpi: int = 150) -> List[str]:
        """
        Convert PDF pages to base64-encoded images
        
        Args:
            pdf_file: Either a file path (str) or a file-like object (Django FileField)
            dpi: DPI for image conversion (default 150)
        
        Returns:
            List of base64-encoded PNG images
        """
        images_base64 = []
        
        # Handle both file paths and file objects (S3/Django FileField)
        if isinstance(pdf_file, str):
            # Local file path
            pdf_document = fitz.open(pdf_file)
        else:
            # File object (from S3 or Django FileField)
            # Read file content into memory
            pdf_file.seek(0)  # Ensure we're at the start
            pdf_bytes = pdf_file.read()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        try:
            # Convert each page to image
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image (matrix for higher DPI)
                zoom = dpi / 72  # 72 is default DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                
                # Encode to base64
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                images_base64.append(img_base64)
        
        finally:
            pdf_document.close()
        
        return images_base64
    
    def analyze_pid_drawing(self, pdf_file) -> Dict[str, Any]:
        """
        Analyze P&ID drawing using OpenAI GPT-4 Vision
        
        Args:
            pdf_file: Either a file path (str) or a Django FileField object
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Convert PDF pages to images
            images_base64 = self.pdf_to_images(pdf_file)
            
            if not images_base64:
                raise ValueError("Failed to convert PDF to images")
            
            # Build message content with all page images
            message_content = [
                {
                    "type": "text",
                    "text": self.ANALYSIS_PROMPT
                }
            ]
            
            # Add each page image
            for idx, img_base64 in enumerate(images_base64):
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}",
                        "detail": "high"
                    }
                })
            
            # Call OpenAI API with vision capabilities
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior oil & gas engineering expert specializing in P&ID verification and design review."
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent technical analysis
            )
            
            # Extract and parse JSON response
            result_text = response.choices[0].message.content
            
            # Log raw response for debugging
            print(f"[DEBUG] OpenAI Raw Response (first 500 chars): {result_text[:500] if result_text else 'EMPTY'}")
            
            if not result_text or not result_text.strip():
                raise ValueError("OpenAI returned empty response")
            
            # Clean potential markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            import json
            try:
                analysis_result = json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON Decode Error: {str(e)}")
                print(f"[ERROR] Problematic text: {result_text[:1000]}")
                raise ValueError(f"OpenAI returned invalid JSON: {str(e)}")
            
            # Validate and enrich response
            if 'issues' not in analysis_result:
                analysis_result['issues'] = []
            
            if 'summary' not in analysis_result:
                analysis_result['summary'] = {
                    'total_issues': len(analysis_result.get('issues', [])),
                    'critical_count': 0,
                    'major_count': 0,
                    'minor_count': 0,
                    'observation_count': 0
                }
            
            if 'drawing_info' not in analysis_result:
                analysis_result['drawing_info'] = {
                    'drawing_number': 'Unknown',
                    'drawing_title': 'Unknown',
                    'revision': 'Unknown',
                    'analysis_date': datetime.now().isoformat()
                }
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {str(e)}")
            raise Exception(f"P&ID analysis failed: AI returned invalid JSON format. {str(e)}")
        except Exception as e:
            print(f"[ERROR] P&ID analysis exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"P&ID analysis failed: {str(e)}")
    
    def generate_report_summary(self, issues: List[Dict]) -> Dict[str, int]:
        """Generate summary statistics from issues"""
        summary = {
            'total_issues': len(issues),
            'approved_count': 0,
            'ignored_count': 0,
            'pending_count': 0,
            'critical_count': 0,
            'major_count': 0,
            'minor_count': 0,
            'observation_count': 0
        }
        
        for issue in issues:
            # Count by status
            status = issue.get('status', 'pending').lower()
            if status == 'approved':
                summary['approved_count'] += 1
            elif status == 'ignored':
                summary['ignored_count'] += 1
            else:
                summary['pending_count'] += 1
            
            # Count by severity
            severity = issue.get('severity', 'observation').lower()
            if severity == 'critical':
                summary['critical_count'] += 1
            elif severity == 'major':
                summary['major_count'] += 1
            elif severity == 'minor':
                summary['minor_count'] += 1
            else:
                summary['observation_count'] += 1
        
        return summary
