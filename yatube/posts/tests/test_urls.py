from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostsURLTests(TestCase):

    URL = {
        'index': '/',
        'group': '/group/testgroup/',
        'profile': '/profile/user1/',
        'post': '/posts/1/',
        'editpost': '/posts/1/edit/',
        'create': '/create/',
        'comment': '/posts/1/comment/',
        'follow_index': '/follow/',
        'profile_follow': '/profile/user1/follow/',
        'profile_unfollow': '/profile/user1/unfollow/',
        'unexisting': '/unexisting_page/',
    }

    TEMPLATES = {
        'index': 'posts/index.html',
        'group': 'posts/group_list.html',
        'profile': 'posts/profile.html',
        'post': 'posts/post_detail.html',
        'create': 'posts/create_post.html',
        'follow_index': 'posts/follow.html',
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='user1')
        cls.user2 = User.objects.create_user(username='user2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост, длинный длинный текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user2)

    def test_url_exists_at_desired_location(self):
        """Страницы, доступные любым пользователям."""
        url_names = [
            self.URL['index'],
            self.URL['group'],
            self.URL['profile'],
            self.URL['post'],
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страницы, которые перенаправяют пользователя на страницу логина."""
        url_names_redirect = [
            'editpost',
            'create',
            'comment',
            'follow_index',
            'profile_follow',
            'profile_unfollow'
        ]
        for url_name in url_names_redirect:
            address = self.URL[url_name]
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + address)

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы, доступные авторизованным пользователям."""
        url_names = [
            self.URL['editpost'],
            self.URL['create'],
            self.URL['follow_index'],
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client_1.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_strange_url_is_not_exists(self):
        """Несуществующая страница."""
        response = self.guest_client.get(self.URL['unexisting'])
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_editing_allowed_only_for_author(self):
        """При попытке редактирования пользователь, не являющийся автором,
         редиректится на страницу поста."""
        response = self.authorized_client_2.get(
            self.URL['editpost'], follow=True)
        self.assertRedirects(response, self.URL['post'])

    def test_comment_redirect_to_post(self):
        """После комментирования пользователь редиректится
         на страницу поста."""
        response = self.authorized_client_1.get(
            self.URL['comment'], follow=True)
        self.assertRedirects(response, self.URL['post'])

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            self.URL['index']: self.TEMPLATES['index'],
            self.URL['group']: self.TEMPLATES['group'],
            self.URL['profile']: self.TEMPLATES['profile'],
            self.URL['post']: self.TEMPLATES['post'],
            self.URL['editpost']: self.TEMPLATES['create'],
            self.URL['create']: self.TEMPLATES['create'],
            self.URL['follow_index']: self.TEMPLATES['follow_index'],
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_1.get(address)
                self.assertTemplateUsed(response, template)
