from __future__ import annotations

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class BrevoAPIError(Exception):
    """Raised when Brevo rejects an email request."""


class BrevoEmailBackend(BaseEmailBackend):
    """Send Django email messages through Brevo's HTTPS transactional API."""

    api_url = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = getattr(settings, "BREVO_API_KEY", "")
        self.timeout = getattr(settings, "EMAIL_TIMEOUT", 15)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            raise BrevoAPIError("BREVO_API_KEY is not configured.")

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
        sender_name, sender_email = self._split_address(message.from_email)
        payload = {
            "sender": {"name": sender_name or "Parlament.Online", "email": sender_email},
            "to": [{"email": address} for address in message.to],
            "subject": message.subject,
        }
        if message.cc:
            payload["cc"] = [{"email": address} for address in message.cc]
        if message.bcc:
            payload["bcc"] = [{"email": address} for address in message.bcc]
        if message.reply_to:
            payload["replyTo"] = {"email": message.reply_to[0]}

        html_body = None
        for alternative, mimetype in (getattr(message, "alternatives", None) or []):
            if mimetype == "text/html":
                html_body = alternative
                break

        if message.content_subtype == "html":
            html_body = message.body
        else:
            payload["textContent"] = message.body
        if html_body is not None:
            payload["htmlContent"] = html_body

        response = requests.post(
            self.api_url,
            headers={"api-key": self.api_key, "Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:500]
            raise BrevoAPIError(f"Brevo API returned HTTP {response.status_code}: {detail}")

    @staticmethod
    def _split_address(value):
        from email.utils import parseaddr
        name, address = parseaddr(value or "")
        return name, address
