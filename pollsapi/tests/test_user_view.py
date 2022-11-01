# IDE: PyCharm
# Project: drf
# Path: pollsapi/tests
# File: test_user.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-06 (y-m-d) 5:56 PM

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIRequestFactory

from pollsapi import views


class TestUserCreate(APITestCase):

    def setUp(self) -> None:
        self.uri = '/api-polls/user/'
        self.request_factory = APIRequestFactory()

    def test_perform_get(self):
        self.request = self.request_factory.get(self.uri)
        resp: Response = views.UserCreate.as_view()(self.request)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_perform_create(self):
        self.request = self.request_factory.post(self.uri, data={'username': 'test', 'password': '12345678'})
        resp: Response = views.UserCreate.as_view()(self.request)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

