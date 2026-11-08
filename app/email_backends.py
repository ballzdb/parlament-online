from __future__ import annotations

import json
from typing import Iterable

import requests
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """Minimal Resend email backend for production SMTP-less setups."""

    def __init__(self, api_key=None, api_url='https://api.resend.com/emails', from_email=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or self._get_setting('RESEND_API_KEY', '')
        self.api_url = api_url or self._get_setting('RESEND_API_URL', 'https://api.resend.com/emails')
        self.from_email = from_email or self._get_setting('DEFAULT_FROM_EMAIL', 'no-reply@parlament-online.local')

    def _get_setting(self, name, default):
        from django.conf import settings

        value = getattr(settings, name, default)
        return value or default

    def send_messages(self, email_messages: Iterable):
        if not email_messages:
            return 0

        sent = 0
        for message in email_messages:
            payload = {
                'from': self.from_email,
                'to': list(message.to),
                'subject': message.subject,
                'text': message.body,
            }
            if getattr(message, 'alternatives', None):
                for alt in message.alternatives:
                    if alt[1] == 'text/html':
                        payload['html'] = alt[0]
                        break
            response = requests.post(
                self.api_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                },
                data=json.dumps(payload),
                timeout=30,
            )
            response.raise_for_status()
            sent += 1
        return sent
