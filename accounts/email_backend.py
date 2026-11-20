from __future__ import annotations

import base64
import os

import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import SafeMIMEText


class ResendAPIError(Exception):
    """Raised when Resend rejects an email request."""


class ResendEmailBackend(BaseEmailBackend):
    """Django email backend that sends mail through Resend's HTTPS API."""

    api_url = "https://api.resend.com/emails"

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = os.getenv("RESEND_API_KEY", "").strip()
        self.timeout = int(os.getenv("RESEND_TIMEOUT", "15"))

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ResendAPIError("RESEND_API_KEY is not configured.")

        sent = 0
        for message in email_messages:
            try:
                self._send_one(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, message):
        payload = {
            "from": message.from_email,
            "to": list(message.to),
            "subject": message.subject,
        }

        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        if message.reply_to:
            payload["reply_to"] = list(message.reply_to)

        html_body = None
        for alternative, mimetype in (message.alternatives or []):
            if mimetype == "text/html":
                html_body = alternative
                break

        if message.content_subtype == "html":
            html_body = message.body
        else:
            payload["text"] = message.body

        if html_body is not None:
            payload["html"] = html_body

        if message.attachments:
            attachments = []
            for attachment in message.attachments:
                if isinstance(attachment, MIMEBase):
                    filename = attachment.get_filename() or "attachment"
                    content = attachment.get_payload(decode=True) or b""
                    mimetype = attachment.get_content_type()
                else:
                    filename, content, mimetype = attachment
                    if isinstance(content, str):
                        content = content.encode("utf-8")
                    mimetype = mimetype or "application/octet-stream"
                attachments.append({
                    "filename": filename,
                    "content": base64.b64encode(content).decode("ascii"),
                })
            payload["attachments"] = attachments

        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:500]
            raise ResendAPIError(
                f"Resend API returned HTTP {response.status_code}: {detail}"
            )
        return response.json()


# Imported here to keep the standard-library email dependency explicit.
from email.mime.base import MIMEBase
