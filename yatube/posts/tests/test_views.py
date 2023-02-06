from http import HTTPStatus

from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test-slug',
            description='Тест-описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Большой тест-пост',
            group=cls.group,
        )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_CREATE_URL = reverse('posts:post_create')
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )

    def setUp(self):
        self.urls_templates_data = [
            (PostViewsTests.INDEX_URL, 'posts/index.html'),
            (PostViewsTests.GROUP_LIST_URL, 'posts/group_list.html'),
            (PostViewsTests.PROFILE_URL, 'posts/profile.html'),
            (PostViewsTests.POST_DETAIL_URL, 'posts/post_detail.html'),
            (PostViewsTests.POST_CREATE_URL, 'posts/create_post.html'),
            (PostViewsTests.POST_EDIT_URL, 'posts/create_post.html'),
        ]

    def test_post_pages_accessible_by_name(self):
        """Проверяем, что URL, генерируемый при помощи
        имени posts:<name>, доступен."""
        for url, _ in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_accordance_templates_reverse(self):
        """Проверяем, что view-функции используют ожидаемые шаблоны."""

        for url, template in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )

    def context_page_obj_is_valid(self, url):
        """Проверяем контекст по ключу 'page_obj'."""
        response = PostViewsTests.author_client.get(url)
        first_object = response.context['page_obj'][0]
        self.assertIsInstance(first_object, Post)
        self.assertEqual(first_object.author, PostViewsTests.author)
        self.assertEqual(first_object.group, PostViewsTests.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        self.context_page_obj_is_valid(PostViewsTests.INDEX_URL)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        self.context_page_obj_is_valid(PostViewsTests.GROUP_LIST_URL)
        response = PostViewsTests.author_client.get(
            PostViewsTests.GROUP_LIST_URL
        )
        first_group = response.context['group']
        self.assertIsInstance(first_group, Group)
        self.assertEqual(first_group, PostViewsTests.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.context_page_obj_is_valid(PostViewsTests.PROFILE_URL)
        response = PostViewsTests.author_client.get(PostViewsTests.PROFILE_URL)
        self.assertEqual(len(response.context['page_obj']), 1)
        first_author = response.context['author']
        self.assertIsInstance(first_author, User)
        self.assertEqual(first_author, PostViewsTests.author)

    def context_post_is_valid(self, url):
        """Проверка контекста по ключу 'post'."""
        response = PostViewsTests.author_client.get(url)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, PostViewsTests.author)
        self.assertEqual(post.group, PostViewsTests.group)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.context_post_is_valid(PostViewsTests.POST_DETAIL_URL)

    def form_fields_is_valid(self, url):
        """Проверка типов полей формы."""
        response = PostViewsTests.author_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        self.form_fields_is_valid(PostViewsTests.POST_CREATE_URL)

    def test_edit_page_show_correct_context(self):
        """Шаблон create_post на странице редактирования записи
        сформирован с правильным контекстом."""
        self.context_post_is_valid(PostViewsTests.POST_EDIT_URL)
        self.form_fields_is_valid(PostViewsTests.POST_EDIT_URL)
        response = PostViewsTests.author_client.get(
            PostViewsTests.POST_EDIT_URL
        )
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_check_group_in_pages(self):
        """Проверка, что запись попала на галвную страницу,
        страницу сообщества и старницу профиля,
        для которых была предназначена."""
        self.post = Post.objects.get(group=self.post.group)
        form_fields = {
            PostViewsTests.INDEX_URL: self.post,
            PostViewsTests.GROUP_LIST_URL: self.post,
            PostViewsTests.PROFILE_URL: self.post
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.author_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_post_is_not_in_incorrect_group(self):
        """Проверка, что запись не попала на страницу сообщества,
        для которой не была предназначена."""
        self.group2 = Group.objects.create(
            title='Тест-группа2',
            slug='test-slug2',
            description='Тест-описание2',
        )
        group_list_url2 = reverse(
            'posts:group_list', kwargs={'slug': f'{self.group2.slug}'}
        )
        response = PostViewsTests.author_client.get(group_list_url2)
        self.assertEqual(len(response.context['page_obj']), 0)
        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertEqual(group, self.group2)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test',
            description='Тест-описание',
        )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.ADDPOSTS = 5

        cls.posts = Post.objects.bulk_create(
            Post(
                author=cls.author,
                text=f'{i + 1} большой тест-пост',
                group=cls.group
            )
            for i in range(settings.NUMBER_ROWS + cls.ADDPOSTS)
        )

    def test_accordance_posts_per_pages(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 5"""

        for url in [
            PostPaginatorTests.INDEX_URL,
            PostPaginatorTests.GROUP_LIST_URL,
            PostPaginatorTests.PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = PostPaginatorTests.author_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.NUMBER_ROWS
                )
                response_second = PostPaginatorTests.author_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    PostPaginatorTests.ADDPOSTS
                )
