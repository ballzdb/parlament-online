from __future__ import annotations

import os
from unittest.mock import Mock, patch

from django.core.mail import EmailMessage
from django.test import SimpleTestCase

from .email_backend import ResendAPIError, ResendEmailBackend


class ResendEmailBackendTests(SimpleTestCase):
    @patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"})
    @patch("accounts.email_backend.requests.post")
    def test_sends_django_email_through_https_api(self, post):
        response = Mock(ok=True)
        response.json.return_value = {"id": "email_test_id"}
        post.return_value = response

        message = EmailMessage(
            subject="Verification",
            body="Your code is 123456",
            from_email="Parlament.Online <no-reply@example.com>",
            to=["student@example.com"],
        )

        sent = ResendEmailBackend().send_messages([message])

        self.assertEqual(sent, 1)
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.resend.com/emails")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer re_test_key")
        self.assertEqual(kwargs["json"]["to"], ["student@example.com"])
        self.assertEqual(kwargs["json"]["text"], "Your code is 123456")

    @patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"})
    @patch("accounts.email_backend.requests.post")
    def test_resend_api_error_is_reported(self, post):
        response = Mock(ok=False, status_code=403, text="Forbidden")
        response.json.return_value = {"message": "Domain not verified"}
        post.return_value = response

        message = EmailMessage(
            subject="Verification",
            body="123456",
            from_email="no-reply@example.com",
            to=["student@example.com"],
        )

        with self.assertRaises(ResendAPIError):
            ResendEmailBackend().send_messages([message])

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_fails_clearly(self):
        with self.assertRaises(ResendAPIError):
            ResendEmailBackend().send_messages([
                EmailMessage("Subject", "Body", "from@example.com", ["to@example.com"])
            ])
