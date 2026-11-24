import csv
from django.test import TestCase

from accounts.models import PRIMARY_ADMIN_EMAIL, User
from analytics.models import PageView
from ideas.models import Idea


class AnalyticsDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email=PRIMARY_ADMIN_EMAIL,
            password='Password123',
            is_active=True,
        )
        self.member = User.objects.create_user(
            email='member@khul.ukr.education',
            password='Password123',
            role=User.Role.MEMBER,
            is_active=True,
        )

    def test_dashboard_is_restricted_to_primary_admin(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get('/analytics/').status_code, 403)

    def test_dashboard_counts_distinct_browsers_including_anonymous(self):
        PageView.objects.create(path='/ideas/', visitor_key='browser-one', user=self.admin)
        PageView.objects.create(path='/ideas/', visitor_key='browser-one', user=self.admin)
        PageView.objects.create(path='/ideas/', visitor_key='browser-two', user=None)
        PageView.objects.create(path='/events/', visitor_key='browser-three', user=None)

        self.client.force_login(self.admin)
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_accounts_30d'], 1)
        self.assertEqual(response.context['anonymous_browsers_30d'], 2)
        self.assertEqual(response.context['active_visitors_30d'], 3)

    def test_csv_export_is_restricted_to_primary_admin(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get('/analytics/export.csv').status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.get('/analytics/export.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])

    def test_csv_export_neutralises_spreadsheet_formulas_in_user_content(self):
        malicious_title = '=HYPERLINK("https://example.com","click")'
        Idea.objects.create(
            title=malicious_title,
            body='Test idea',
            author=self.admin,
        )
        self.client.force_login(self.admin)
        response = self.client.get('/analytics/export.csv')
        rows = list(csv.reader(response.content.decode('utf-8-sig').splitlines()))
        idea_row = next(row for row in rows if row[0] == 'idea')
        self.assertEqual(idea_row[2], "'" + malicious_title)
