import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Некоторый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def forms_data(self):
        """Возвращает различные варианты данных форм Post для тестирования"""
        return [
            {
                'text': 'Тестовый текст',
            },
            {
                'text': 'Тестовый текст 2',
                'group': self.group.pk,
            }
        ]

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Проверим и для наличия, и для отсутствия группы
        for form_data in self.forms_data():
            posts_count = Post.objects.count()
            response = self.auth_client.post(
                reverse('posts:post_create'),
                data=form_data,
                follow=True
            )
            self.assertRedirects(response, reverse(
                'posts:profile', kwargs={'username': 'user'})
            )
            self.assertEqual(Post.objects.count(), posts_count + 1)
            self.assertTrue(Post.objects.filter(
                text=form_data['text']).exists())

    def test_edit_post(self):
        """Редактирование записи в Post."""
        # Проверим и для наличия, и для отсутствия группы
        for form_data in self.forms_data():
            posts_count = Post.objects.count()
            response = self.auth_client.post(
                reverse('posts:post_edit', kwargs={'post_id': 1}),
                data=form_data,
                follow=True
            )
            self.assertRedirects(response, reverse(
                'posts:post_detail', kwargs={'post_id': 1})
            )
            # Проверим, что кол-во не изменилось
            self.assertEqual(Post.objects.count(), posts_count)
            self.assertFalse(Post.objects.filter(
                text='Некоторый пост').exists())
            self.assertTrue(Post.objects.filter(
                text=form_data['text']).exists())

    def test_create_post_guest(self):
        """Создания постов под гостем не происходит."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_guest(self):
        """Редактирования поста гостем не происходит."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        # Проверим, что кол-во не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text='Некоторый пост').exists())
        self.assertFalse(Post.objects.filter(text=form_data['text']).exists())

    def test_edit_post_another_author(self):
        """Редактирования поста не его автором не происходит."""
        self.user2 = User.objects.create_user(username='user2')
        self.auth_client2 = Client()
        self.auth_client2.force_login(self.user2)
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        response = self.auth_client2.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': 1})
        )
        # Проверим, что кол-во не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text='Некоторый пост').exists())
        self.assertFalse(Post.objects.filter(text=form_data['text']).exists())

    def test_create_post_with_image(self):
        """Валидная форма с картинкой создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text']).exists())

    def test_create_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comments_count = self.post.comments.count()
        form_data = {'text': 'Тестовый комментарий'}
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        comments = response.context['comments']
        self.assertTrue(comments.filter(text=form_data['text']).exists())
