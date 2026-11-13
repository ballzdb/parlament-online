from django.test import TestCase

from .models import User


class LogoutMethodTests(TestCase):
    def test_logout_requires_post_and_post_clears_session(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Password123!',
            is_active=True,
        )
        self.client.force_login(user)

        get_response = self.client.get('/accounts/logout/')
        self.assertEqual(get_response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

        post_response = self.client.post('/accounts/logout/')
        self.assertEqual(post_response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_control_is_a_post_form_with_csrf(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Password123!',
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.get('/')

        self.assertContains(response, '<form method="post" action="/accounts/logout/" class="nav-logout-form">')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
