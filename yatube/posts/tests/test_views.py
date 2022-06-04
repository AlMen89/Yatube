import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from os.path import basename
from posts.models import Follow, Group, Post, User

from yatube.settings import POSTS_PER_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user2 = User.objects.create_user(username='user2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='testgroup2',
            description='Тестовое описание 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_gif = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, длинный текст',
            group=cls.group,
            image=cls.uploaded_gif,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_posts', kwargs={'slug': 'testgroup'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'user'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': 1}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': 1}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_object(self, post):
        """Проверяет, что содержимое поста соответствует ожидаемому."""
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, 'Тестовый пост, длинный текст')
        self.assertEqual(post.group, self.group)
        self.assertEqual(basename(post.image.path), self.uploaded_gif.name)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.check_object(first_object)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'testgroup'})
        )
        self.assertEqual(
            response.context.get('group'),
            get_object_or_404(Group, slug='testgroup'))
        first_object = response.context['page_obj'][0]
        self.check_object(first_object)

    def test_group_posts_not_in_another_group(self):
        """Пост не попадает в группу, для которой не предназначен."""
        response = self.auth_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'testgroup2'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse(
            'posts:profile', kwargs={'username': 'user'})
        )
        self.assertEqual(
            response.context.get('author'),
            get_object_or_404(User, username='user'))
        self.assertEqual(response.context.get('posts_count'), 1)
        first_object = response.context['page_obj'][0]
        self.check_object(first_object)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(
            response.context.get('post'),
            get_object_or_404(Post, id=1)
        )
        self.assertEqual(response.context.get('posts_count'), 1)

    # Поля, из которых должна состоять форма поста
    POST_FORM_FIELDS = {
        'text': forms.fields.CharField,
        'group': forms.fields.ChoiceField,
        'image': forms.fields.ImageField,
    }

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse('posts:post_create'))
        self.assertEqual(response.context.get('is_edit'), False)
        for value, expected in self.POST_FORM_FIELDS.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 1})
        )
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertEqual(
            response.context.get('post'), get_object_or_404(Post, id=1))
        for value, expected in self.POST_FORM_FIELDS.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        """Список записей главной страницы сайта кэшируется"""
        new_post = Post.objects.create(
            author=self.user,
            text='Ещё один пост',
        )
        response = self.auth_client.get(reverse('posts:index'))
        Post.objects.filter(pk=new_post.pk).delete()
        new_response = self.auth_client.get(reverse('posts:index'))
        # Проверим, что ответ не изменился, т.к. был закэширован
        self.assertEqual(response.content, new_response.content)

    def test_can_follow(self):
        """Авторизованный пользователь может подписываться
         на других пользователей и удалять их из подписок."""
        response = self.auth_client.get(reverse(
            'posts:profile_follow', kwargs={'username': 'user2'}),
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'user2'}))
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.user2).exists())
        response = self.auth_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': 'user2'}),
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'user2'}))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user2).exists())

    def test_follow_index(self):
        """Запись пользователя появляется в ленте тех, кто на него подписан."""
        Follow.objects.create(user=self.user, author=self.user2)
        post2 = Post.objects.create(
            author=self.user2,
            text='Тестовый пост второго пользователя',
            group=self.group,
        )
        response = self.auth_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, post2)
        # Проверим, что в ленте остальных пользователей она не появляется
        self.auth_client2 = Client()
        self.auth_client2.force_login(self.user2)
        response2 = self.auth_client2.get(reverse('posts:follow_index'))
        self.assertEqual(len(response2.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user2 = User.objects.create_user(username='user2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
            description='Тестовое описание',
        )
        post_bulk = []
        for i in range(1, 2 * POSTS_PER_PAGE):
            # Проставим группу только для первой страницы + 2 элемента
            group = cls.group if i <= POSTS_PER_PAGE + 2 else None
            # Проставим автора user только для первой страницы + 1 элемент
            author = cls.user if i <= POSTS_PER_PAGE + 1 else cls.user2
            post = Post(
                author=author,
                text=f'Тестовый пост №{i}',
                group=group,
            )
            post_bulk.append(post)
        Post.objects.bulk_create(post_bulk)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_first_page(self):
        """На первой странице умещается POSTS_PER_PAGE постов"""
        response = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_page(self):
        """На второй странице умещается POSTS_PER_PAGE-1 постов"""
        response = self.auth_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE - 1)

    def test_first_page_group(self):
        """На первой странице группы умещается POSTS_PER_PAGE постов"""
        response = self.auth_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'testgroup'})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_page_group(self):
        """На второй странице группы умещается 2 поста"""
        response = self.auth_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'testgroup'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_first_page_author(self):
        """На первой странице автора умещается POSTS_PER_PAGE постов"""
        response = self.auth_client.get(reverse(
            'posts:profile', kwargs={'username': 'user'})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_second_page_author(self):
        """На второй странице автора умещается 1 пост"""
        response = self.auth_client.get(reverse(
            'posts:profile', kwargs={'username': 'user'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)
