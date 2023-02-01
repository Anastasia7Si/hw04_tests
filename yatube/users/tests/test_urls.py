from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


User = get_user_model()


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testUser1')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

        cls.SIGNUP = '/auth/signup/'
        cls.LOGOUT = '/auth/logout/'
        cls.LOGIN = '/auth/login/'
        cls.PASSWORD_CHANGE = '/auth/password_change/'
        cls.PASSWORD_CHANGE_DONE = '/auth/password_change/done/'
        cls.PASSWORD_RESET = '/auth/password_reset/'
        cls.PASSWORD_RESET_DONE = '/auth/password_reset/done/'
        cls.RESET_CONFIRM = '/auth/reset/<uidb64>/<token>/'
        cls.RESET_DONE = '/auth/reset/done/'
        cls.NON_EXISTING_PAGE = '/existing_page/'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testAuthorized1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.public_urls = [
            (UserURLTests.SIGNUP, 'users/signup.html'),
            (UserURLTests.LOGIN, 'users/login.html'),
            (UserURLTests.PASSWORD_RESET, 'users/password_reset_form.html'),
            (
                UserURLTests.PASSWORD_RESET_DONE,
                'users/password_reset_done.html'),
            (UserURLTests.RESET_CONFIRM, 'users/password_reset_confirm.html'),
            (UserURLTests.RESET_DONE, 'users/password_reset_complete.html'),
        ]

        self.private_urls = [
            (UserURLTests.PASSWORD_CHANGE, 'users/password_change_form.html'),
            (
                UserURLTests.PASSWORD_CHANGE_DONE,
                'users/password_change_done.html'),
            (UserURLTests.LOGOUT, 'users/logged_out.html'),
        ]

    def test_existing_pages(self):

        for url, _ in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_unexisting_page(self):
        response = self.guest_client.get(UserURLTests.NON_EXISTING_PAGE)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_accordance_urls_templates(self):

        for url, template in self.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )
