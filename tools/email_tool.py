"""
DocuForge AI — Email Tool

LangGraph tool for agents to send email reports.
Uses SMTP with environment-based configuration for portability.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EmailInput(BaseModel):
    """Input schema for email delivery tool."""

    recipient: str = Field(..., description="Email address to send report to")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body (plain text or HTML)")
    is_html: bool = Field(default=False, description="Whether body is HTML formatted")


def send_report_email(recipient: str, subject: str, body: str, is_html: bool = False) -> bool:
    """
    Send an email report via SMTP.
    Returns True on success, False on any failure. Never raises exceptions.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.warning("SMTP not fully configured — email tool unavailable")
        return False

    try:
        smtp_port = int(smtp_port)

        # Create message
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = subject

        # Add body
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Upgrade to TLS
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info("Email sent to %s: %s", recipient, subject)
        return True
    except Exception as e:
        logger.warning("Failed to send email: %s", str(e))
        return False


def get_email_tool() -> dict:
    """
    Return a LangGraph tool dict for sending report emails.
    Use in agent: tool_choice = {"type": "function", "function": {"name": "email"}}
    """
    return {
        "name": "email",
        "description": "Send a report email to a recipient. Useful for delivering analysis results or evaluation summaries.",
        "input_schema": EmailInput.model_json_schema(),
        "function": lambda input_data: send_report_email(
            input_data.get("recipient", ""),
            input_data.get("subject", ""),
            input_data.get("body", ""),
            input_data.get("is_html", False),
        ),
    }
