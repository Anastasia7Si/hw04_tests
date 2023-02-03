
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class SignUpViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_client = Client()

        cls.SIGNUP = reverse('users:signup')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_signup_page_uses_correct_template(self):
        response = self.user_client.get(SignUpViewsTests.SIGNUP)
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_signup_page_show_correct_context(self):
        response = self.user_client.get(SignUpViewsTests.SIGNUP)
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
