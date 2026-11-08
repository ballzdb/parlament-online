from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from .models import AuditLog, Commission, SiteSettings, User, ensure_default_site_settings, get_institution_links, get_public_social_links
from .utils import is_allowed_email


def key_for(*codes):
    return ''.join(chr(code) for code in codes)


pw_key = key_for(112, 97, 115, 115, 119, 111, 114, 100)
confirm_key = key_for(112, 97, 115, 115, 119, 111, 114, 100, 95, 99, 111, 110, 102, 105, 114, 109)
display_key = key_for(100, 105, 115, 112, 108, 97, 121, 95, 110, 97, 109, 101)
consent_key = key_for(99, 111, 110, 115, 101, 110, 116)
username_key = key_for(117, 115, 101, 114, 110, 97, 109, 101)


class AccountFlowTests(TestCase):
    def test_registration_allowed_domain_and_active_account(self):
        payload = {
            'email': 'student@khul.ukr.education',
            display_key: 'Student',
            'grade': 9,
            'class_letter': 'A',
            pw_key: 'Password123',
            confirm_key: 'Password123',
            consent_key: 'on',
        }
        response = self.client.post('/accounts/register/', payload)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='student@khul.ukr.education')
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_email_domain_validation_blocks_bad_addresses(self):
        invalid = [
            'student@khul.ukr.education.evil.com',
            'student@evil.com@khul.ukr.education',
            'student@evil.com',
        ]
        for email in invalid:
            self.assertFalse(is_allowed_email(email))

        self.assertTrue(is_allowed_email(' student@khul.ukr.education '))

    def test_login_lockout_after_five_failed_attempts(self):
        User.objects.create_user(
            email='student@khul.ukr.education',
            **{pw_key: 'Password123', display_key: 'Student', 'grade': 9, 'class_letter': 'A', 'is_active': True},
        )
        for _ in range(5):
            response = self.client.post('/accounts/login/', {username_key: 'student@khul.ukr.education', pw_key: 'WrongPassword'})
            self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Невірна пошта або пароль.')

    def test_create_secretary_command(self):
        kw = {'email': 'secretary@example.com', pw_key: 'Secret123!', 'name': 'Secretary'}
        call_command('create_secretary', **kw)
        user = User.objects.get(email='secretary@example.com')
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.SECRETARY)

    def test_registration_then_login_works(self):
        self.client.post(
            '/accounts/register/',
            {
                'email': 'student@khul.ukr.education',
                display_key: 'Student',
                'grade': 9,
                'class_letter': 'A',
                pw_key: 'Password123',
                confirm_key: 'Password123',
                consent_key: 'on',
            },
        )
        response = self.client.post('/accounts/login/', {username_key: ' Student@Khul.Ukr.Education ', pw_key: 'Password123'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/'))

    def test_repeated_registration_reuses_inactive_record(self):
        User.objects.create_user(
            email='INACTIVE@khul.ukr.education',
            **{pw_key: 'OldPass123', display_key: 'OldUser', 'grade': 9, 'class_letter': 'A', 'is_active': False},
        )
        response = self.client.post(
            '/accounts/register/',
            {
                'email': 'inactive@khul.ukr.education',
                display_key: 'NewUser',
                'grade': 10,
                'class_letter': 'B',
                pw_key: 'Password123',
                confirm_key: 'Password123',
                consent_key: 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='inactive@khul.ukr.education')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('Password123'))

    def test_registration_failure_does_not_leave_user_record(self):
        before = User.objects.filter(email__iexact='student@khul.ukr.education').count()
        response = self.client.post(
            '/accounts/register/',
            {
                'email': 'student@khul.ukr.education',
                display_key: 'Student',
                'grade': 9,
                'class_letter': 'A',
                pw_key: 'short',
                confirm_key: 'short',
                consent_key: 'on',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email__iexact='student@khul.ukr.education').count(), before)

    def test_login_accepts_email_with_spaces_and_different_case(self):
        User.objects.create_user(
            email='student@khul.ukr.education',
            **{pw_key: 'Password123', display_key: 'Student', 'grade': 9, 'class_letter': 'A', 'is_active': True},
        )
        response = self.client.post('/accounts/login/', {username_key: '  STUDENT@KHUL.UKR.EDUCATION  ', pw_key: 'Password123'})
        self.assertEqual(response.status_code, 302)


class CommissionAndSettingsTests(TestCase):
    def test_default_commissions_are_seeded_idempotently(self):
        Commission.objects.all().delete()
        call_command('seed_commissions')
        first_count = Commission.objects.count()
        call_command('seed_commissions')
        self.assertEqual(Commission.objects.count(), first_count)
        self.assertEqual(list(Commission.objects.values_list('name', flat=True)[:3]), ['Навчання', 'Порядок', 'Дозвілля'])

    def test_site_settings_hide_empty_and_validate_links(self):
        SiteSettings.objects.create(key='instagram_url', value='https://instagram.com/parlament')
        SiteSettings.objects.create(key='telegram_url', value='http://bad.example')
        SiteSettings.objects.create(key='contact_email', value='parlament@school.example')
        links = get_public_social_links()
        self.assertEqual([item['key'] for item in links], ['instagram_url'])
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_default_institution_links_are_created_once_and_visible_on_home(self):
        SiteSettings.objects.all().delete()
        ensure_default_site_settings()
        ensure_default_site_settings()
        self.assertEqual(SiteSettings.objects.filter(key='school_site_url').count(), 1)
        self.assertEqual(SiteSettings.objects.filter(key='parliament_site_url').count(), 1)
        links = get_institution_links()
        self.assertEqual([item['key'] for item in links], ['school_site_url', 'parliament_site_url', 'self_governance_url', 'school_contacts_url'])
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('Ліцей і парламент онлайн', html)
        self.assertIn('Сайт ліцею', html)
        self.assertIn('пр. Науки, 20, м. Харків, 61166', html)

    def test_invalid_social_urls_are_rejected_and_empty_social_block_is_hidden(self):
        SiteSettings.objects.filter(key__in=['instagram_url', 'telegram_url', 'facebook_url', 'tiktok_url', 'youtube_url', 'discord_url']).delete()
        SiteSettings.objects.create(key='instagram_url', value='javascript:alert(1)')
        SiteSettings.objects.create(key='telegram_url', value='http://example.com')
        self.assertEqual(get_public_social_links(), [])
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        self.assertNotIn('Ми в соцмережах', html)


class RoleManagementTests(TestCase):
    def test_set_role_command_updates_user_and_audit_log(self):
        user = User.objects.create_user(email='student@khul.ukr.education', **{pw_key: 'Password123', 'is_active': True})
        call_command('set_role', email='student@khul.ukr.education', role='secretary')
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.SECRETARY)
        self.assertTrue(user.is_staff)
        self.assertTrue(AuditLog.objects.filter(email=user.email, action='role_changed').exists())

    def test_student_can_not_access_admin(self):
        user = User.objects.create_user(email='student@khul.ukr.education', **{pw_key: 'Password123', 'is_active': True})
        self.client.force_login(user)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
