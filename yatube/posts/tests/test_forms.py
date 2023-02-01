import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
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
            group=cls.group
        )

        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_CREATE_URL = reverse('posts:post_create')
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testAuthorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def count_posts(self):
        return Post.objects.count()

    def test_authorized_client_create_form(self):
        post_aut_detail_url = reverse(
            'posts:profile', kwargs={'username': 'testAuthorized'}
        )
        text = 'Текст авторизованного пользователя'
        create_form_data = {
            'text': text,
            'group': PostFormTests.group.pk,
        }
        response = self.authorized_client.post(
            PostFormTests.POST_CREATE_URL,
            data=create_form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=text,
            ).exists()
        )
        self.assertRedirects(response, post_aut_detail_url)
        self.assertEqual(self.count_posts(), 2)

    def test_guest_client_not_allowed_create_form(self):
        post_guest_redirect_url = '/auth/login/?next=/create/'
        text = 'Текст анонимного пользователя'
        create_form_data = {
            'text': text,
        }
        response = self.guest_client.post(
            PostFormTests.POST_CREATE_URL,
            data=create_form_data,
        )
        self.assertFalse(
            Post.objects.filter(
                text=text,
            ).exists()
        )
        self.assertRedirects(response, post_guest_redirect_url)
        self.assertEqual(self.count_posts(), 1)

    def test_author_edit_form(self):
        text = 'Отредактированный текст'
        edit_form_data = {
            'text': text,
            'group': self.group.pk,
        }
        edit_response = self.author_client.post(
            PostFormTests.POST_EDIT_URL,
            data=edit_form_data,
        )
        self.assertTrue(
            Post.objects.filter(
                text=text,
            ).exists()
        )
        self.assertRedirects(edit_response, PostFormTests.POST_DETAIL_URL)
        self.assertEqual(self.count_posts(), 1)
