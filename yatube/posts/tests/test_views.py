import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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

        for url, _ in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_accordance_templates_reverse(self):

        for url, template in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )

    def context_page_obj_is_valid(self, url):
        response = PostViewsTests.author_client.get(url)
        first_object = response.context['page_obj'][0]
        self.assertIsInstance(first_object, Post)
        self.assertEqual(first_object.author, PostViewsTests.author)
        self.assertEqual(first_object.group, PostViewsTests.group)

    def test_index_page_show_correct_context(self):
        self.context_page_obj_is_valid(PostViewsTests.INDEX_URL)

    def test_group_list_page_show_correct_context(self):
        self.context_page_obj_is_valid(PostViewsTests.GROUP_LIST_URL)
        response = PostViewsTests.author_client.get(
            PostViewsTests.GROUP_LIST_URL
        )
        first_group = response.context['group']
        self.assertIsInstance(first_group, Group)
        self.assertEqual(first_group, PostViewsTests.group)

    def test_profile_page_show_correct_context(self):
        self.context_page_obj_is_valid(PostViewsTests.PROFILE_URL)
        response = PostViewsTests.author_client.get(PostViewsTests.PROFILE_URL)
        self.assertEqual(len(response.context['page_obj']), 1)
        first_author = response.context['author']
        self.assertIsInstance(first_author, User)
        self.assertEqual(first_author, PostViewsTests.author)

    def context_post_is_valid(self, url):
        response = PostViewsTests.author_client.get(url)
        post = response.context['post']
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, PostViewsTests.author)
        self.assertEqual(post.group, PostViewsTests.group)

    def test_post_detail_page_show_correct_context(self):
        self.context_post_is_valid(PostViewsTests.POST_DETAIL_URL)

    def form_fields_is_valid(self, url):
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
        self.form_fields_is_valid(PostViewsTests.POST_CREATE_URL)

    def test_edit_page_show_correct_context(self):
        self.context_post_is_valid(PostViewsTests.POST_EDIT_URL)
        self.form_fields_is_valid(PostViewsTests.POST_EDIT_URL)
        response = PostViewsTests.author_client.get(
            PostViewsTests.POST_EDIT_URL
        )
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_check_group_in_pages(self):
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
