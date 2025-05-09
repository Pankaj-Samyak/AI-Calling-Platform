import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

def send_password_email(email: str, user_password: str):
    try:
        # Email content
        subject = "Your AI Calling Platform Login Credentials"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h3>AI Calling Platform - User Credentials</h3>
            <p>Hello,</p>
            <p>Your login credentials for the <strong>AI Calling</strong> are:</p>
            <ul>
            <li><strong>Email:</strong> {email}</li>
            <li><strong>Password:</strong> {user_password}</li>
            </ul>
            <p>Please keep this information confidential.</p>
            <p>Thank you,<br/>The Samyak Team</p>
        </body>
        </html>
        """
        # Create email
        msg = MIMEMultipart()
        msg["From"] = formataddr(("Support Team", os.getenv("MAIL_USERNAME")))
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, 'html'))
        # Send email
        with smtplib.SMTP(os.getenv("MAIL_HOST") , os.getenv("MAIL_PORT")) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USERNAME") ,os.getenv("MAIL_PASSWORD") )
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def forget_password(email: str, user_password: str):
    try:
        # Email content
        subject = "Reset Your AI Calling Password"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h3>AI Calling - Password Reset</h3>
            <p>Hello,</p>
            <p>You recently requested to reset your password for the <strong>AI Calling</strong>.</p>
            <p>Your new login credentials are:</p>
            <ul>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>New Password:</strong> {user_password}</li>
            </ul>
            <p>For security reasons, please change your password after logging in.</p>
            <p>If you didn’t request a password reset, please contact support immediately.</p>
            <p>Thank you,<br/>The Samyak Team</p>
        </body>
        </html>
        """

        # Create email
        msg = MIMEMultipart()
        msg["From"] = formataddr(("Support Team", os.getenv("MAIL_USERNAME")))
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, 'html'))
        # Send email
        with smtplib.SMTP(os.getenv("MAIL_HOST") , os.getenv("MAIL_PORT")) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USERNAME") ,os.getenv("MAIL_PASSWORD") )
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
