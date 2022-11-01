# IDE: PyCharm
# Project: drf
# Path: pollsapi/tests
# File: test_login_view.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-06 (y-m-d) 5:57 PM

from rest_framework.response import Response
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class TestLogin(APITestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.credentials = {'username': 'test', 'password': '12345678'}
        self.user: User = User.objects.create_user(**self.credentials)
        self.auth_token = Token.objects.create(user=self.user)
        self.uri = '/api-polls/login/'

    def test_login(self):
        """
            tests login for further token authentication
        """
        # session login
        is_logged = self.client.login(username='test_232', password='dfdf')
        self.assertFalse(is_logged)

        is_logged = self.client.login(**self.credentials)
        self.assertTrue(is_logged)

        self.client.logout()

        # token login
        resp: Response = self.client.post(self.uri, self.credentials)
        self.assertDictEqual({
            'username': self.credentials['username'],
            'token': self.auth_token.key
        }, resp.data)

