# IDE: PyCharm
# Project: drf
# Path: pollsapi/tests
# File: test_vote_view.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-07 (y-m-d) 5:33 PM

# tests for
# path("poll/<int:pk>/choice/<int:choice_pk>/vote/", views.Vote.as_view(), name="vote"),
# class Vote(generics.CreateAPIView):

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from pollsapi import models, serializers
from pollsapi.tests.test_choice_view import ChoiceMixin


class VoteMixin(ChoiceMixin):
    serializer_class = serializers.VoteSerializer


class TestChoiceList(VoteMixin, APITestCase):

    # path("poll/<int:pk>/choice/<int:choice_pk>/vote/", views.Vote.as_view(), name="vote"),
    view_name = 'pollsapi:vote'
    view_name_kwargs_map = {'pk': 'poll_id', 'choice_pk': 'id'}

    def test_perform_token_login(self):
        choice = self.create_fixtures()[0]

        resp = self.get_response('get', choice, HTTP_AUTHORIZATION='Token fake_token')
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

        # get is not supported - 'get' login is available as status.HTTP_405_METHOD_NOT_ALLOWED
        resp = self.get_response(
            'get', choice, HTTP_AUTHORIZATION='Token {}'.format(choice.poll.created_by.auth_token.key)
        )
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_perform_other(self):
        """
            methods besides 'post' are not available
        """

        choice = self.create_fixtures()[0]

        # 'get' tested in test_perform_token_login()
        token_value = f'Token {choice.poll.created_by.auth_token.key}'
        for method in ("put", "patch", "delete", 'head'):
            with self.subTest(method=method):
                resp = self.get_response(method, choice, HTTP_AUTHORIZATION=token_value)
                self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_perform_create(self):
        choices = self.create_fixtures()
        choice = choices[0]

        # test not authenticated - fail
        resp: Response = self.get_response('post', choice)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)
        self.assertEqual(0, models.Vote.objects.count())

        user = self.users[0]
        token_value = f'Token {user.auth_token.key}'
        # test authenticated - success
        resp = self.get_response('post', choice, HTTP_AUTHORIZATION=token_value)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, models.Vote.objects.count())

        # test authenticated - unsuccessful - cause second attempt on same poll
        resp = self.get_response('post', choice, HTTP_AUTHORIZATION=token_value)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(1, models.Vote.objects.count())

        user = self.users[1]
        # test session authenticated creation - good
        islogged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(islogged)

        resp = self.get_response('post', choice)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(2, models.Vote.objects.count())

        # second attempt vote for poll that was voted already - error
        resp = self.get_response('post', choice)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        test_resp_content = b'{"non_field_errors":["You are voted on this poll"]}'
        self.assertEqual(test_resp_content, resp.content)
        self.assertEqual(2, models.Vote.objects.count())

        # poll that does not exists - error
        url_params = {'poll_id': 0, 'id': choice.pk}
        resp = self.get_response('post', url_params)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        test_resp_content = b'{"non_field_errors":["The choice is not appropriate for a poll\'s question"]}'
        self.assertEqual(test_resp_content, resp.content)
        self.assertEqual(2, models.Vote.objects.count())

        # choice that does not exists - error
        url_params = {'poll_id': choice.poll_id, 'id': 0}
        resp = self.get_response('post', url_params)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        test_resp_content = b'{"non_field_errors":["Invalid pk \\"0\\" - object does not exist."]}'
        self.assertEqual(test_resp_content, resp.content)
        self.assertEqual(2, models.Vote.objects.count())

        # choice that is not appropriate to poll - error
        poll = models.Poll.objects.filter(choices__isnull=True).get()
        url_params = {'poll_id': poll.pk, 'id': choice.id}
        resp = self.get_response('post', url_params)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        test_resp_content = b'{"non_field_errors":["The choice is not appropriate for a poll\'s question"]}'
        self.assertEqual(test_resp_content, resp.content)
        self.assertEqual(2, models.Vote.objects.count())

        # This is not mandatory but we will create dummy choice for poll that has no choices
        # and repeat again (almost)
        dummy_choice = models.Choice.objects.create(choice_text='dummy_choice', poll=poll)
        url_params = {'poll_id': choice.poll_id, 'id': dummy_choice.pk}
        resp = self.get_response('post', url_params)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

        test_resp_content = b'{"non_field_errors":["The choice is not appropriate for a poll\'s question"]}'
        self.assertEqual(test_resp_content, resp.content)
        self.assertEqual(2, models.Vote.objects.count())
