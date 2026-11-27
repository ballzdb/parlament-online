from django.test import TestCase


class RemovedResearchFeedbackPageTests(TestCase):
    def test_removed_feedback_page_returns_not_found(self):
        response = self.client.get('/ideas/feedback/')
        self.assertEqual(response.status_code, 404)

    def test_removed_feedback_page_is_not_linked_from_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '/ideas/feedback/')
