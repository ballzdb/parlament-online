from django.test import TestCase


class ResearchFeedbackPageTests(TestCase):
    def test_feedback_page_is_public_and_embeds_current_survey(self):
        response = self.client.get('/ideas/feedback/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Опитування учнів')
        self.assertContains(
            response,
            'https://docs.google.com/forms/d/e/1FAIpQLScKXjSa2R2RlZT7DF0gJJPklTYVcNSxsvwHXT3oHClcGAHSqQ/viewform?embedded=true',
        )
        self.assertContains(response, 'анонімне')

    def test_feedback_page_is_linked_in_main_navigation(self):
        response = self.client.get('/')
        self.assertContains(response, '/ideas/feedback/')
