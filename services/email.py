# app/email.py
import os
import resend
from dotenv import load_dotenv
from fastapi_users import BaseUserManager, models

from app.db.models import User

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

class CustomEmailManager:
    
    def __init__(self):
        self.from_email = os.getenv("EMAILS_FROM_EMAIL")
        self.from_name = os.getenv("EMAILS_FROM_NAME")
        self.frontend_url = os.getenv("FRONTEND_URL")
    
    async def send_password_reset(self, user: User, token: str, user_manager: BaseUserManager):
        """
        Send password reset email using FastAPI Users token
        """
        reset_url = f"{self.frontend_url}/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .reset-btn {{ background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CAR E-RESCUE</h1>
                    <p>Password Reset Request</p>
                </div>
                <div class="content">
                    <h2>Hello {user.name},</h2>
                    <p>You requested to reset your password.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="reset-btn">Reset Password</a>
                    </p>
                    <p>Or use this link:<br>{reset_url}</p>
                    <p><em>This link expires in {user_manager.reset_password_token_lifetime_seconds // 3600} hours.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset - CAR E-RESCUE
        
        Hello {user.email},
        
        Reset your password using this link:
        {reset_url}
        
        This link expires in {user_manager.reset_password_token_lifetime_seconds // 3600} hours.
        
        If you didn't request this, please ignore this email.
        """
        
        try:
            response = resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [user.email],
                "subject": "Reset Your Password - CAR E-RESCUE",
                "html": html_content,
                "text": text_content
            })
            return True
        except Exception as e:
            return False