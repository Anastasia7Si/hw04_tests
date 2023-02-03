from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


INDEX = '/'
CREATE = '/create/'
CREATE_REVERSE = '/auth/login/?next=/create/'
NON_EXISTING_PAGE = '/existing_page/'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Длинный тестовый пост',
        )

        cls.GROUP_POSTS = f'/group/{cls.group.slug}/'
        cls.PROFILE = f'/profile/{cls.author.username}/'
        cls.POST_DETAIL = f'/posts/{cls.post.id}/'
        cls.EDIT = f'/posts/{cls.post.id}/edit/'
        cls.EDIT_REVERSE = f'/auth/login/?next=/posts/{cls.post.id}/edit/'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testAuthorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.public_urls = [
            (INDEX, 'posts/index.html'),
            (PostURLTests.GROUP_POSTS, 'posts/group_list.html'),
            (PostURLTests.PROFILE, 'posts/profile.html'),
            (PostURLTests.POST_DETAIL, 'posts/post_detail.html'),
        ]

        self.private_urls = [
            (CREATE, 'posts/create_post.html'),
            (PostURLTests.EDIT, 'posts/create_post.html'),
        ]

    def test_existing_pages(self):

        for url, template in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_unexisting_page(self):
        response = self.guest_client.get(NON_EXISTING_PAGE)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_authorized_client_creates_post(self):
        response = self.authorized_client.get(CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(CREATE, follow=True)
        self.assertRedirects(response, CREATE_REVERSE)

    def test_only_author_edites_post(self):
        response = self.author_client.get(PostURLTests.EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_edit_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(PostURLTests.EDIT, follow=True)
        self.assertRedirects(response, PostURLTests.EDIT_REVERSE)

    def test_post_edit_url_redirect_authorized_on_post_detail(self):
        response = self.authorized_client.get(PostURLTests.EDIT, follow=True)
        self.assertRedirects(response, PostURLTests.POST_DETAIL)

    def test_post_edit_url_redirect_other_author_on_post_detail(self):
        self.other_author = User.objects.create_user(username='otherAuthor')
        self.other_author_client = Client()
        self.other_author_client.force_login(self.other_author)
        self.other_post = Post.objects.create(
            author=self.other_author,
            text='Другой большой пост',
        )

        response = self.other_author_client.get(PostURLTests.EDIT, follow=True)
        self.assertRedirects(response, PostURLTests.POST_DETAIL)

    def test_accordance_urls_templates(self):

        for url, template in self.private_urls + self.private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )
