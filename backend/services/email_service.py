from __future__ import annotations

import os

import resend

from models.user import UserOut

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")


def _get_client() -> None:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("RESEND_API_KEY environment variable is not set")
    resend.api_key = api_key


def send_verification_email(user: UserOut, token: str) -> None:
    _get_client()
    verify_url = f"{FRONTEND_ORIGIN}/verify-email?token={token}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0D0B1A; color: #E2E8F0; padding: 32px;">
      <div style="max-width: 480px; margin: 0 auto; background: #1E1B3A; border-radius: 16px; padding: 32px; border: 1px solid rgba(124,58,237,0.3);">
        <h1 style="font-size: 24px; margin: 0 0 16px; color: #C4B5FD;">Verify your email</h1>
        <p style="line-height: 1.6; margin: 0 0 24px;">Click the button below to verify your email address for MindMirror.</p>
        <a href="{verify_url}" style="display: inline-block; background: linear-gradient(135deg, #7C3AED, #EC4899); color: white; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 600; font-size: 16px;">Verify Email</a>
        <p style="margin-top: 24px; font-size: 14px; color: #94A3B8;">This link expires in 24 hours. If you didn't create an account, you can safely ignore this email.</p>
      </div>
    </body>
    </html>
    """
    params = {
        "from": FROM_EMAIL,
        "to": [user.email],
        "subject": "Verify your email — MindMirror",
        "html": html,
    }
    resend.Emails.send(params)
