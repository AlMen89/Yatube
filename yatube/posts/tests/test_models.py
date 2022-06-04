from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, длинный длинный текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментария, длинный длинный текст',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user2,
        )

    def check_some_fields(self, model, metafield, field_values):
        """Проверка метаданных в полях заданной модели"""
        for field, expected_value in field_values.items():
            with self.subTest(field=field):
                model_field = model._meta.get_field(field)
                checking_attr = getattr(model_field, metafield)
                self.assertEqual(checking_attr, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses_post = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        self.check_some_fields(
            PostModelTest.post, "verbose_name", field_verboses_post)
        field_verboses_group = {
            'title': 'Название группы',
            'slug': 'Название группы для url',
            'description': 'Описание группы',
        }
        self.check_some_fields(
            PostModelTest.group, "verbose_name", field_verboses_group)
        field_verboses_comment = {
            'post': 'Пост',
            'author': 'Автор комментария',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        self.check_some_fields(
            PostModelTest.comment, "verbose_name", field_verboses_comment)
        field_verboses_follow = {
            'user': 'Подписавшийся пользователь',
            'author': 'Пользователь, на которого подписались',
        }
        self.check_some_fields(
            PostModelTest.follow, "verbose_name", field_verboses_follow)

    def test_help_test(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_post = {
            'text': 'Текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        self.check_some_fields(
            PostModelTest.post, "help_text", field_help_post)
        field_help_comment = {
            'text': 'Текст нового комментария',
        }
        self.check_some_fields(
            PostModelTest.comment, "help_text", field_help_comment)

    def test_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))

    def test_comment_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        comment = PostModelTest.comment
        expected_comment_name = comment.text[:15]
        self.assertEqual(expected_comment_name, str(comment))
