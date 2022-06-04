from http import HTTPStatus

from django.test import Client, TestCase


class AboutTests(TestCase):

    URL = {
        'author': '/about/author/',
        'tech': '/about/tech/',
    }

    TEMPLATES = {
        'author': 'about/author.html',
        'tech': 'about/tech.html',
    }

    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Страницы доступны."""
        url_names = [
            self.URL['author'],
            self.URL['tech'],
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            self.URL['author']: self.TEMPLATES['author'],
            self.URL['tech']: self.TEMPLATES['tech'],
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
