from http import HTTPStatus
from django.test import TestCase


class CoreTests(TestCase):
    def test_error_page(self):
        """Страница 404."""
        response = self.client.get('/unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
