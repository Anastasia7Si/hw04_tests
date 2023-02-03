from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

POST_CREATE_URL = reverse('posts:post_create')


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
            text='Большой тест-пост для проведения тестов',
            group=cls.group
        )

        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testAuthorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_create_form(self):
        posts_count = Post.objects.count()
        text = 'Текст авторизованного пользователя'
        create_form_data = {
            'text': text,
            'group': PostFormTests.group.pk,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=create_form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=text,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)

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
        self.assertEqual(Post.objects.count(), 1)
