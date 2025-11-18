"""
CV HTML to PDF Conversion Service
Handles conversion of HTML CV content to PDF using multiple methods:
1. Playwright (best quality, uses Chromium browser engine)
2. xhtml2pdf (fallback, pure Python)

All browser automation is done in subprocesses to avoid event loop issues on Windows.
"""

import asyncio
import json
import base64
import tempfile
import sys
import subprocess
import platform
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


class CVHTML2PDFService:
    """
    Service for converting HTML CV content to PDF.
    """
    
    def __init__(self):
        """Initialize the service."""
        # Get the data/cv directory path
        self.data_cv_dir = Path(__file__).parent.parent.parent / 'data' / 'cv'
        self.data_cv_dir.mkdir(parents=True, exist_ok=True)
    
    def _prepare_html_content(self, html_content: str) -> str:
        """
        Prepare HTML content for PDF conversion while preserving CVEditor styles and layout.
        This ensures the PDF output matches what's seen in the CVEditor preview.
        
        Args:
            html_content: Raw HTML content (should already be cleaned by CVEditor's cleanHtmlForExport)
            
        Returns:
            Prepared HTML content with PDF-specific adjustments
        """
        # Ensure DOCTYPE if missing
        if not html_content.strip().startswith('<!DOCTYPE'):
            html_content = '<!DOCTYPE html>\n' + html_content
        
        # Ensure charset meta tag
        if 'charset' not in html_content[:500].lower():
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', '<head><meta charset="UTF-8">', 1)
            elif '<html' in html_content:
                html_content = html_content.replace('<html', '<html><head><meta charset="UTF-8"></head>', 1)
        
        # Remove preview-specific styles that CVEditor might have missed
        # Remove grey background, box-shadow, and preview margins from body
        html_content = re.sub(
            r'body\s*\{[^}]*background:\s*#e5e7eb[^}]*\}',
            lambda m: re.sub(r'background:\s*#e5e7eb[^;]*;?', '', m.group(0), flags=re.IGNORECASE),
            html_content,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        # Remove box-shadow from containers (preview effect)
        html_content = re.sub(
            r'box-shadow:\s*0\s+4px\s+12px\s+rgba\(0,0,0,0\.2\)[^;]*;?',
            '',
            html_content,
            flags=re.IGNORECASE
        )
        
        # Remove preview-specific margins (like "0 auto 40px auto" for page separation)
        html_content = re.sub(
            r'margin:\s*0\s+auto\s+40px\s+auto[^;]*;?',
            '',
            html_content,
            flags=re.IGNORECASE
        )
        
        # REMOVED: @page rule override - now preserves original @page margins from frontend HTML
        # The original @page rule from the HTML will be used as-is
        
        # REMOVED: Body margin/padding override - now preserves original body margins from frontend HTML
        # Only ensure white background (remove preview grey background)
        body_style_pattern = r'body\s*\{[^}]*\}'
        if re.search(body_style_pattern, html_content, re.IGNORECASE | re.DOTALL):
            def ensure_clean_body(match):
                body_content = match.group(0)
                # Remove preview-specific grey background only
                body_content = re.sub(r'background:\s*#e5e7eb[^;]*;?', '', body_content, flags=re.IGNORECASE)
                body_content = re.sub(r'padding:\s*20px[^;]*;?', '', body_content, flags=re.IGNORECASE)
                # Only ensure white background if not set, preserve original margin/padding
                if 'background' not in body_content.lower():
                    body_content = body_content.replace('{', '{ background: white; ', 1)
                return body_content
            
            html_content = re.sub(body_style_pattern, ensure_clean_body, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Ensure container matches CVEditor preview settings exactly
        # CVEditor uses: width: 210mm, padding: 8mm 10mm (top/bottom 8mm, left/right 10mm)
        container_pattern = r'\.container\s*\{[^}]*\}'
        if re.search(container_pattern, html_content, re.IGNORECASE | re.DOTALL):
            def clean_container_styles(match):
                container_content = match.group(0)
                # Remove box-shadow (preview effect) only
                container_content = re.sub(r'box-shadow:[^;]*;?', '', container_content, flags=re.IGNORECASE)
                # Remove preview-specific margins (page separation in editor)
                container_content = re.sub(r'margin:\s*0\s+auto\s+40px\s+auto[^;]*;?', '', container_content, flags=re.IGNORECASE)
                # Ensure width matches CVEditor: 210mm
                if 'width:\s*210mm' not in container_content.lower() and 'width:\s*198mm' not in container_content.lower():
                    # Only set if width is not already set to 210mm or 198mm
                    if 'width:' not in container_content.lower():
                        container_content = container_content.replace('{', '{ width: 210mm; ', 1)
                # Ensure max-width is set for A4 if not present
                if 'max-width' not in container_content.lower():
                    container_content = container_content.replace('{', '{ max-width: 210mm; ', 1)
                # Preserve original padding (should be 8mm 10mm from CVEditor)
                return container_content
            
            html_content = re.sub(container_pattern, clean_container_styles, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Ensure font-size CSS rules are preserved and not modified
        # Check if any font-size rules were accidentally removed
        # This is a safety check to ensure typography is preserved
        
        # Add CSS to ensure fonts render at correct size in PDF
        # Match browser rendering exactly - preserve all font-size declarations
        pdf_font_style = '''
    <style>
        /* Ensure fonts render at correct size in PDF - match browser exactly */
        html {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        /* Preserve all font sizes exactly as specified - no scaling or modification */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
    </style>
'''
        # Insert PDF font style after existing styles or in head
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', pdf_font_style + '</head>', 1)
        elif '</style>' in html_content:
            # Insert after last style tag
            last_style_pos = html_content.rfind('</style>')
            if last_style_pos != -1:
                html_content = html_content[:last_style_pos + 8] + pdf_font_style + html_content[last_style_pos + 8:]
        
        return html_content
    
    def _save_html_file(self, html_content: str, prefix: str = 'cv_export') -> Tuple[Path, str]:
        """
        Save HTML content to a file in data/cv folder.
        
        Args:
            html_content: HTML content to save
            prefix: Filename prefix
            
        Returns:
            Tuple of (file_path, timestamp)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        html_file_path = self.data_cv_dir / f'{prefix}_{timestamp}.html'
        
        try:
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return html_file_path, timestamp
        except Exception as e:
            print(f"Warning: Failed to save HTML to {html_file_path}: {e}")
            return html_file_path, timestamp
    
    def _create_playwright_script(self, html_file_path: str) -> str:
        """
        Create the Playwright subprocess script.
        
        Args:
            html_file_path: Path to HTML file (escaped for Python string)
            
        Returns:
            Script content as string
        """
        return f'''import sys
import json
import base64

try:
    from playwright.sync_api import sync_playwright
    
    # Read HTML from file
    html_file_path = r"{html_file_path}"
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        result = {{"success": False, "error": "Failed to read HTML file: " + str(e)}}
        print(json.dumps(result))
        sys.exit(1)
    
    # Use sync Playwright API
    with sync_playwright() as p:
        # Launch browser with cache disabled to ensure fresh content
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--disable-gpu', '--no-sandbox']
        )
        try:
            # Create context with cache disabled
            context = browser.new_context(
                ignore_https_errors=True,
                bypass_csp=True
            )
            # Disable cache for this context
            context.set_extra_http_headers({{
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }})
            page = context.new_page()
            # Set viewport to match A4 dimensions exactly as shown in CVEditor
            # A4: 210mm × 297mm = 794px × 1123px at 96 DPI (standard browser DPI)
            # CVEditor shows container at 210mm width, so viewport should match A4 exactly
            scale_factor = 1.0
            # Use exact A4 dimensions at 96 DPI to match browser rendering
            page.set_viewport_size({{"width": 794, "height": 1123}})
            # Emulate screen media to match CVEditor preview (not print media)
            page.emulate_media(media='screen')
            # Set content directly - no network requests, so no caching issues
            page.set_content(html_content, wait_until='load')
            # Wait for fonts and layout to fully render (matching browser behavior)
            page.wait_for_timeout(1000)  # Wait for fonts/content to render
            
            pdf_bytes = page.pdf(
                format='A4',
                margin={{'top': '0mm', 'right': '0mm', 'bottom': '0mm', 'left': '0mm'}},
                print_background=True,
                prefer_css_page_size=False,  # Disable to allow scale to work properly
                display_header_footer=False,
                scale=scale_factor  # Scale up to 120% for larger text and content
            )
            
            if pdf_bytes and len(pdf_bytes) > 0:
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                result = {{"success": True, "pdf_base64": pdf_base64, "size": len(pdf_bytes)}}
                print(json.dumps(result))
                sys.exit(0)
            else:
                result = {{"success": False, "error": "Empty PDF generated"}}
                print(json.dumps(result))
                sys.exit(1)
        finally:
            context.close()
            browser.close()
            
except ImportError as e:
    result = {{"success": False, "error": "playwright not installed: " + str(e)}}
    print(json.dumps(result))
    sys.exit(1)
except Exception as e:
    result = {{"success": False, "error": str(e)}}
    print(json.dumps(result))
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    def _run_subprocess_windows(self, script_path: str) -> Tuple[int, bytes, bytes]:
        """Run subprocess on Windows using subprocess.run in a thread."""
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            timeout=120,
            text=False
        )
        return result.returncode, result.stdout or b"", result.stderr or b""
    
    async def _run_subprocess_unix(self, script_path: str) -> Tuple[int, bytes, bytes]:
        """Run subprocess on Unix-like systems using asyncio."""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
        return process.returncode, stdout or b"", stderr or b""
    
    def _parse_subprocess_result(self, returncode: int, stdout: bytes, stderr: bytes) -> bytes:
        """
        Parse subprocess result and return PDF bytes.
        
        Args:
            returncode: Process return code
            stdout: Standard output bytes
            stderr: Standard error bytes
            
        Returns:
            PDF bytes
            
        Raises:
            ValueError: If conversion failed
        """
        stdout_text = stdout.decode('utf-8', errors='ignore')
        stderr_text = stderr.decode('utf-8', errors='ignore')
        
        try:
            result = json.loads(stdout_text)
            if result.get('success'):
                pdf_base64 = result.get('pdf_base64')
                if not pdf_base64:
                    raise ValueError("No pdf_base64 in result")
                return base64.b64decode(pdf_base64)
            else:
                error_msg = result.get('error', 'Unknown error from subprocess')
                raise ValueError(f"playwright subprocess failed: {error_msg}")
        except json.JSONDecodeError:
            error_msg = stderr_text if stderr_text else stdout_text if stdout_text else "Unknown error"
            if returncode != 0:
                raise ValueError(f"playwright subprocess failed (code {returncode}): {error_msg}")
            else:
                raise ValueError(f"playwright subprocess returned invalid response: {stdout_text[:500]}")
    
    async def convert_with_playwright(
        self, 
        html_content: str, 
        output_path: Optional[str] = None,
        save_debug_files: bool = True
    ) -> Optional[bytes]:
        """
        Convert HTML to PDF using Playwright in a subprocess.
        
        Args:
            html_content: HTML content to convert
            output_path: Optional path to save PDF
            save_debug_files: Whether to save HTML and PDF files to data/cv for debugging
            
        Returns:
            PDF bytes, or None if conversion failed
            
        Raises:
            ValueError: If PDF generation fails
        """
        # Prepare and save HTML content
        # Add a unique identifier to ensure fresh content (prevents any caching)
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        html_content = self._prepare_html_content(html_content)
        # Add unique identifier comment to HTML to prevent any caching
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head><!-- PDF Export ID: {unique_id} - {datetime.now().isoformat()} -->', 1)
        html_file_path, timestamp = self._save_html_file(html_content, 'cv_export')
        print(f"[PDF] Generated unique export ID: {unique_id}, saved HTML to: {html_file_path.name}")
        
        # Escape file path for use in script
        html_file_path_str = str(html_file_path.absolute()).replace('\\', '\\\\')
        
        # Create and write subprocess script
        script_content = self._create_playwright_script(html_file_path_str)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as script_file:
                script_file.write(script_content)
                script_path = script_file.name
            
            try:
                # Run subprocess (platform-specific)
                if platform.system() == 'Windows':
                    returncode, stdout, stderr = await asyncio.to_thread(
                        self._run_subprocess_windows, script_path
                    )
                else:
                    returncode, stdout, stderr = await self._run_subprocess_unix(script_path)
                
                # Parse result
                pdf_bytes = self._parse_subprocess_result(returncode, stdout, stderr)
                
                # Save PDF if output path provided
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(pdf_bytes)
                
                # Save debug PDF if requested
                if save_debug_files:
                    pdf_file_path = self.data_cv_dir / f'cv_export_{timestamp}.pdf'
                    try:
                        with open(pdf_file_path, 'wb') as f:
                            f.write(pdf_bytes)
                    except Exception as e:
                        print(f"Warning: Failed to save debug PDF: {e}")
                
                return pdf_bytes
                
            finally:
                # Clean up script file
                try:
                    Path(script_path).unlink()
                except Exception:
                    pass
                    
        except asyncio.TimeoutError:
            raise ValueError("playwright PDF generation timed out after 2 minutes")
        except FileNotFoundError:
            raise ValueError("Python interpreter not found")
        except Exception as e:
            error_msg = str(e)
            if "playwright" not in error_msg.lower():
                error_msg = f"playwright subprocess error: {error_msg}"
            raise ValueError(error_msg)
    
    async def convert_with_xhtml2pdf(
        self, 
        html_content: str, 
        output_path: Optional[str] = None,
        save_debug_files: bool = True
    ) -> Optional[bytes]:
        """
        Convert HTML to PDF using xhtml2pdf (pure Python fallback).
        
        Args:
            html_content: HTML content to convert
            output_path: Optional path to save PDF
            save_debug_files: Whether to save HTML and PDF files to data/cv for debugging
            
        Returns:
            PDF bytes, or None if conversion failed
            
        Raises:
            ValueError: If PDF generation fails
        """
        try:
            from xhtml2pdf import pisa
            from io import BytesIO
        except ImportError:
            raise ValueError("xhtml2pdf not installed. Install with: pip install xhtml2pdf")
        
        # Prepare HTML content
        html_content = self._prepare_html_content(html_content)
        
        # Post-process HTML to remove unsupported CSS
        html_content = self._post_process_html_for_xhtml2pdf(html_content)
        
        # Save HTML to file for debugging
        if save_debug_files:
            html_file_path, timestamp = self._save_html_file(html_content, 'cv_export_xhtml2pdf')
        
        # Convert HTML to PDF
        pdf_buffer = BytesIO()
        
        try:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer, encoding='utf-8')
            
            if pisa_status.err:
                raise ValueError(f"xhtml2pdf error: {pisa_status.err}")
            
            pdf_bytes = pdf_buffer.getvalue()
            
            if not pdf_bytes or len(pdf_bytes) == 0:
                raise ValueError("xhtml2pdf generated empty PDF")
            
            # Save PDF if output path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
            
            # Save debug PDF if requested
            if save_debug_files:
                pdf_file_path = self.data_cv_dir / f'cv_export_xhtml2pdf_{timestamp}.pdf'
                try:
                    with open(pdf_file_path, 'wb') as f:
                        f.write(pdf_bytes)
                except Exception as e:
                    print(f"Warning: Failed to save debug PDF: {e}")
            
            return pdf_bytes
            
        except Exception as e:
            error_msg = str(e)
            if "xhtml2pdf" not in error_msg.lower() and "pisa" not in error_msg.lower():
                error_msg = f"xhtml2pdf error: {error_msg}"
            raise ValueError(error_msg)
    
    def _post_process_html_for_xhtml2pdf(self, html_content: str) -> str:
        """
        Post-process HTML to remove CSS features not supported by xhtml2pdf.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Processed HTML content
        """
        # Remove unsupported CSS at-rules
        patterns = [
            (r'@media\s+[^{]+\{[^}]*\}', ''),  # @media queries
            (r'@keyframes\s+\w+\s*\{[^}]*\}', ''),  # @keyframes
            (r'@supports\s+[^{]+\{[^}]*\}', ''),  # @supports
        ]
        
        for pattern, replacement in patterns:
            html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
        
        return html_content
    
    async def convert_to_pdf(
        self, 
        html_content: str, 
        output_path: Optional[str] = None,
        save_debug_files: bool = True
    ) -> Optional[bytes]:
        """
        Convert HTML to PDF using multiple methods in order of quality:
        1. Playwright (best CSS support, uses Chromium browser engine)
        2. xhtml2pdf (fallback, pure Python)
        
        Args:
            html_content: HTML content to convert
            output_path: Optional path to save PDF
            save_debug_files: Whether to save HTML and PDF files to data/cv for debugging
            
        Returns:
            PDF bytes, or None if conversion failed
            
        Raises:
            ValueError: If all PDF generation methods fail
        """
        # Try Playwright first (best quality, excellent CSS support)
        try:
            return await self.convert_with_playwright(html_content, output_path, save_debug_files)
        except (ImportError, ValueError) as e:
            # Fall back to xhtml2pdf
            return await self.convert_with_xhtml2pdf(html_content, output_path, save_debug_files)


# Singleton instance
_cv_html2pdf_service: Optional[CVHTML2PDFService] = None


def get_cv_html2pdf_service() -> CVHTML2PDFService:
    """
    Get or create the singleton CV HTML to PDF service instance.
    
    Returns:
        CVHTML2PDFService instance
    """
    global _cv_html2pdf_service
    if _cv_html2pdf_service is None:
        _cv_html2pdf_service = CVHTML2PDFService()
    return _cv_html2pdf_service

