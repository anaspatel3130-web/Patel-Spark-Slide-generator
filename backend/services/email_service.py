"""
backend/services/email_service.py
---------------------------------
Automated notification service for Patel'Spark.
Dispatches real-time email notifications whenever a prospective user submits
an Access Request on the platform to anaspatel3130@gmail.com.

Supports:
1. Standard SMTP (Gmail, Outlook, Amazon SES, SendGrid, custom mail servers).
2. Resend REST API (zero extra dependencies, cloud/serverless friendly).
3. Graceful fallback logging when credentials are not yet configured or during local testing.
"""

import json
import logging
import os
import smtplib
import ssl
import urllib.request
import urllib.error
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from backend.config import (
    NOTIFICATION_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_TLS,
    SMTP_SSL,
    RESEND_API_KEY,
)

logger = logging.getLogger("patelspark.email")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class EmailNotificationService:
    """
    Handles generation and transmission of transactional notifications to platform administrators.
    """

    @classmethod
    def send_access_request_alert(cls, request_data: Dict[str, Any]) -> bool:
        """
        Sends an email alert to the platform owner (anaspatel3130@gmail.com)
        detailing the new access request.
        """
        recipient = NOTIFICATION_EMAIL or "anaspatel3130@gmail.com"
        applicant_name = request_data.get("name") or "Prospective User"
        applicant_email = request_data.get("email") or "Unknown Email"
        department = request_data.get("department") or "Not Specified"
        reason = request_data.get("reason") or "No justification provided."
        req_id = request_data.get("id") or "New"
        created_at = request_data.get("created_at")

        if isinstance(created_at, datetime):
            timestamp_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            timestamp_str = str(created_at) if created_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = f"[Patel'Spark] New Access Request #{req_id} from {applicant_name}"

        # 1. Plain Text Version
        text_body = f"""Patel'Spark Access Request Alert
=====================================
A new user has submitted a request to access the Patel'Spark Automation Engine.

Applicant Details:
------------------
- Request ID: #{req_id}
- Full Name: {applicant_name}
- Work Email: {applicant_email}
- Department / Team: {department}
- Submission Date: {timestamp_str}

Business Justification:
-----------------------
{reason}

Action Required:
----------------
To review, approve, or reject this request, please log in to your Patel'Spark Admin Dashboard:
https://patelspark-ai.vercel.app/

(This is an automated notification dispatched to {recipient})
"""

        # 2. Modern HTML Version (Patel'Spark Navy & Spark Amber Palette)
        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>New Access Request</title>
</head>
<body style="margin: 0; padding: 0; background-color: #e9eef4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #e9eef4; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08); border: 1px solid #d5dee8;">
          <!-- Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 30px; text-align: left; border-bottom: 3px solid #ea580c;">
              <table width="100%">
                <tr>
                  <td>
                    <span style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                      Patel’<span style="color: #f97316;">Spark</span>
                    </span>
                    <div style="font-size: 11px; color: #fbbf24; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; margin-top: 2px;">
                      Automation Slide Generator
                    </div>
                  </td>
                  <td align="right">
                    <span style="background-color: rgba(249, 115, 22, 0.2); color: #fed7aa; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; border: 1px solid rgba(249, 115, 22, 0.4);">
                      NEW REQUEST #{req_id}
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 28px 30px;">
              <h2 style="margin: 0 0 10px 0; font-size: 18px; font-weight: 700; color: #0f172a;">
                New User Access Request Submitted
              </h2>
              <p style="margin: 0 0 20px 0; font-size: 14px; color: #475569; line-height: 1.5;">
                A new user has submitted a request for access to the <strong>Patel'Spark</strong> platform. Please review the applicant details below:
              </p>

              <!-- Applicant Details Card -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 22px;">
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; width: 35%; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Applicant Name</td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; color: #0f172a;">{applicant_name}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Work Email</td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; color: #0284c7;">
                    <a href="mailto:{applicant_email}" style="color: #0284c7; text-decoration: none;">{applicant_email}</a>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Department / Team</td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #1e293b;">{department}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Submitted At</td>
                  <td style="padding: 12px 16px; font-size: 13px; color: #475569;">{timestamp_str}</td>
                </tr>
              </table>

              <!-- Business Justification Box -->
              <div style="margin-bottom: 24px;">
                <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px;">Business Justification:</div>
                <div style="background-color: #fff7ed; border-left: 3px solid #f97316; padding: 12px 16px; border-radius: 4px; font-size: 13px; color: #7c2d12; line-height: 1.5;">
                  "{reason}"
                </div>
              </div>

              <!-- Call To Action Button -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center" style="padding: 10px 0 20px 0;">
                    <a href="https://patelspark-ai.vercel.app/" style="background: linear-gradient(135deg, #ea580c 0%, #f97316 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-size: 14px; font-weight: 700; display: inline-block; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.35);">
                      Review &amp; Approve in Admin Portal &rarr;
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                You can approve the request to generate a single-use invite token or reject it from the Admin dashboard.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #0f172a; padding: 16px 30px; text-align: center; border-top: 1px solid #1e293b;">
              <span style="font-size: 11px; color: #94a3b8;">
                Patel'Spark &copy; 2026. Automated notification dispatched to <strong>{recipient}</strong>.
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        # Method A: Try Resend REST API if key provided (best for serverless / Vercel)
        if RESEND_API_KEY:
            try:
                resend_ok = cls._send_via_resend(recipient, subject, text_body, html_body)
                if resend_ok:
                    logger.info(f"[EMAIL_SERVICE] Dispatched access request notification to {recipient} via Resend API.")
                    return True
            except Exception as e:
                logger.warning(f"[EMAIL_SERVICE] Resend API attempt failed: {e}. Falling back to SMTP.")

        # Method B: Standard SMTP (e.g., Gmail smtp.gmail.com:587)
        if SMTP_USER and SMTP_PASSWORD:
            try:
                smtp_ok = cls._send_via_smtp(recipient, subject, text_body, html_body)
                if smtp_ok:
                    logger.info(f"[EMAIL_SERVICE] Dispatched access request notification to {recipient} via SMTP ({SMTP_HOST}).")
                    return True
            except Exception as e:
                logger.error(f"[EMAIL_SERVICE] SMTP delivery to {recipient} failed: {e}")

        # Method C: Graceful notification logging
        # If SMTP credentials are not yet configured in environment variables,
        # log the full formatted alert so the administrator still receives the request in logs
        # without crashing the prospective user's signup flow!
        logger.info(
            f"[EMAIL_SERVICE] Access request #{req_id} received from {applicant_name} ({applicant_email}).\n"
            f"Notification target: {recipient}\n"
            f"Department: {department}\n"
            f"Reason: {reason}\n"
            f"To enable live Gmail delivery to {recipient}, configure SMTP_USER & SMTP_PASSWORD (or RESEND_API_KEY) in your environment variables."
        )
        return False

    @classmethod
    def _send_via_smtp(cls, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        Sends email via SMTP with STARTTLS or SSL.
        """
        from_email = SMTP_FROM_EMAIL or SMTP_USER
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        context = ssl.create_default_context()

        if SMTP_SSL or SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_TLS:
                    server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(from_email, [to_email], msg.as_string())

        return True

    @classmethod
    def _send_via_resend(cls, to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        Sends email via Resend API using standard urllib.request (zero extra dependencies).
        """
        payload = {
            "from": SMTP_FROM_EMAIL or "Patel'Spark Notifications <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "text": text_content,
            "html": html_content,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "PatelSpark-SlideGenerator/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return 200 <= response.status < 300
