from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='Тест-слаг',
            description='Тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест-пост',
            group=cls.group
        )

        cls.LENGTH_TEXT = 15

    def test_model_post_have_correct_str_text(self):
        post = PostModelTest.post
        post_text = post.text[:PostModelTest.LENGTH_TEXT]
        self.assertEqual(str(post), post_text)

    def test_model_group_have_correct_str_title(self):
        group = PostModelTest.group
        group_title = group.title
        self.assertEqual(str(group), group_title)

    def test_post_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Запись',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_verbose_name(self):
        group = PostModelTest.group
        field_verboses = {
            'title': 'Имя группы',
            'slug': 'Адрес',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        post = PostModelTest.post
        field_help = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
