import pdfkit
import os
from typing import Dict, Any
from datetime import datetime
import tempfile
import logging

class PDFService:
    def __init__(self):
        self.options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }
    
    def generate_enrollment_summary(self, session_data: Dict[str, Any], session_id: str) -> str:
        try:
            html_content = self._create_html_template(session_data, session_id)
            
            temp_dir = tempfile.gettempdir()
            pdf_filename = f"enrollment_summary_{session_id}.pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            pdfkit.from_string(html_content, pdf_path, options=self.options)
            
            logging.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
        except Exception as e:
            logging.error(f"PDF generation error: {str(e)}")
            raise
    
    def _create_html_template(self, session_data: Dict[str, Any], session_id: str) -> str:
        current_date = datetime.utcnow().strftime("%B %d, %Y")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Membership Enrollment Summary</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 25px;
                }}
                .section h3 {{
                    color: #007bff;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
                .label {{
                    font-weight: bold;
                    color: #495057;
                }}
                .value {{
                    color: #212529;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #6c757d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Membership Enrollment Summary</h1>
                <p>Generated on {current_date}</p>
                <p>Session ID: {session_id}</p>
            </div>
            
            <div class="section">
                <h3>Personal Information</h3>
                <div class="info-row">
                    <span class="label">Full Name:</span>
                    <span class="value">{session_data.get('name', 'Not provided')}</span>
                </div>
                <div class="info-row">
                    <span class="label">Email Address:</span>
                    <span class="value">{session_data.get('email', 'Not provided')}</span>
                </div>
                <div class="info-row">
                    <span class="label">Company:</span>
                    <span class="value">{session_data.get('company', 'Not provided')}</span>
                </div>
                <div class="info-row">
                    <span class="label">Job Title:</span>
                    <span class="value">{session_data.get('job_title', 'Not provided')}</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Membership Details</h3>
                <div class="info-row">
                    <span class="label">Program Type:</span>
                    <span class="value">{session_data.get('program_type', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="label">How did you hear about us:</span>
                    <span class="value">{session_data.get('referral_source', 'Not provided')}</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Enrollment Status</h3>
                <div class="info-row">
                    <span class="label">Status:</span>
                    <span class="value">{session_data.get('status', 'In Progress')}</span>
                </div>
                <div class="info-row">
                    <span class="label">Completion Date:</span>
                    <span class="value">{session_data.get('completion_date', current_date)}</span>
                </div>
            </div>
            
            <div class="footer">
                <p>This document was automatically generated by the AI Membership Enrollment System.</p>
                <p>For questions or support, please contact our membership team.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
