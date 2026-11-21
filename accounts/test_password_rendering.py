from django.test import SimpleTestCase

from .forms import RegistrationForm


class RegistrationPasswordRenderingTests(SimpleTestCase):
    def test_password_is_not_echoed_when_registration_form_has_errors(self):
        form = RegistrationForm(data={
            "email": "student@example.com",
            "password": "SensitivePass123",
            "display_name": "Student",
            "school_class": "9-А",
        })

        self.assertFalse(form.is_valid())
        self.assertNotIn("SensitivePass123", form.as_p())
