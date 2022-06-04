from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from .forms import CreationForm
from posts.models import User


class UsersTests(TestCase):

    URL = {
        'signup': '/auth/signup/',
    }

    TEMPLATES = {
        'signup': 'users/signup.html',
    }

    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Страница регистрации доступна."""
        response = self.guest_client.get(self.URL['signup'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_use_correct_template(self):
        """URL-адрес страницы регистрации использует соответствующий шаблон."""
        response = self.guest_client.get(self.URL['signup'])
        self.assertTemplateUsed(response, self.TEMPLATES['signup'])

    def test_signup_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени users:signup, доступен."""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_page_uses_correct_template(self):
        """При запросе к users:signup применяется шаблон users/signup.html."""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertTemplateUsed(response, self.TEMPLATES['signup'])

    def test_signup_page_get_new_user_form(self):
        """На страницу регистрации в контексте передаётся
        форма для создания нового пользователя"""
        response = self.guest_client.get(reverse('users:signup'))
        context_form = response.context.get('form')
        self.assertIsInstance(context_form, CreationForm)

    def test_create_user(self):
        """Валидная форма создает пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'username': 'Ivan',
            'email': 'Ivan@yandex.ru',
            'password1': 'Qwertyas123',
            'password2': 'Qwertyas123',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertRedirects(response, reverse('posts:index'))
