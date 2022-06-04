from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_urls_accessible_by_names(self):
        """URL, генерируемые при помощи имен, доступны."""
        pages_names_templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
