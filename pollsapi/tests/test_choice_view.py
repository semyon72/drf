# IDE: PyCharm
# Project: drf
# Path: pollsapi/tests
# File: test_choice_view.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-06 (y-m-d) 6:02 PM

# tests for
# path("poll/<int:pk>/choice/", views.ChoiceList.as_view(), name="choice_list"),
# path("poll/<int:pk>/choice/<int:choice_pk>/", views.ChoiceDetail.as_view(), name="choice_detail"),

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from pollsapi import models, serializers
from pollsapi.tests.utils import ClientToolMixin


class ChoiceMixin(ClientToolMixin):

    serializer_class = serializers.ChoiceSerializer

    def create_polls(self) -> list[models.Poll]:
        results = []
        self.assertGreater(len(self.users), 2, 'This test relies on 3+ users.')

        question = 'poll: question_{username}'
        for user in self.users[1:3]:
            data = {'question': question.format(username=user.username), 'created_by': user}
            poll = models.Poll.objects.create(**data)
            results.append(poll)

        return results

    def get_choice_kwargs(self, seq_num, poll) -> dict:
        choice_text_msg = 'choice #{number} for question[{question}]'
        choice_text = choice_text_msg.format(number=seq_num, question=poll.question)
        return {'choice_text': choice_text, 'poll': poll}

    def create_fixtures(self) -> list[models.Choice]:
        """
        It will create 2 polls 0 - for self.users[0], 1 - for self.users[1] and 1 - for self.users[2]
        and choices for it
        0 choices for poll self.user[1]
        2 choices for self.users[2]
        It does not test an authentication process

        Why in this way - I think, It should be unpredictable behaviour, almost.
        """
        polls = self.create_polls()
        user = self.users[2]
        poll = [poll for poll in polls if poll.created_by == user]
        self.assertEqual(1, len(poll), f'Can\'t find poll in {polls} for user {user}')

        result = []
        poll = poll[0]
        model = models.Choice
        for i in range(2):
            choice = model.objects.create(
                **self.get_choice_kwargs(i, poll)
            )
            result.append(choice)

        res_choices = list(models.Choice.objects.filter(poll__created_by=user))
        self.assertEqual(2, len(res_choices))
        self.assertListEqual(result, res_choices)

        res_choices = models.Choice.objects.filter(poll__created_by=self.users[1])
        self.assertEqual(0, len(res_choices))

        return result


class TestChoiceList(ChoiceMixin, APITestCase):

    # path("poll/<int:pk>/choice/", views.ChoiceList.as_view(), name="choice_list"),
    view_name = 'pollsapi:choice_list'
    view_name_kwargs_map = {'pk': 'id'}

    def test_perform_token_login(self):
        self.dummy_poll = self.create_polls()[0]
        super().test_perform_token_login()

    def get_token_login_url_params(self):
        return self.dummy_poll

    def test_perform_create(self):
        poll = self.create_polls()[0]

        # test not authenticated - fail
        data = self.get_choice_kwargs(1, poll)
        data.pop('poll')

        resp: Response = self.get_response('post', poll, data=data)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)
        self.assertEqual(0, models.Choice.objects.count())

        user = self.users[0]
        # test token authenticated creation  - unsuccessful, cause user is not owner
        self.assertNotEqual(user, poll.created_by)
        resp = self.get_response('post', poll, data=data, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        test_resp_content = b'{"detail":"You can not create choice for this poll"}'
        self.assertEqual(test_resp_content, resp.content)

        user = poll.created_by
        # test token authenticated creation  - successful
        resp = self.get_response('post', poll, data=data, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.check_response_single_object(resp)

        # test session authenticated creation - good
        islogged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(islogged)

        resp = self.get_response('post', poll, data=data)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.check_response_single_object(resp)

    def test_perform_list(self):
        data = self.create_fixtures()
        self.assertEqual(2, len(data))

        response = self.get_response('get', data[0].poll)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertListEqual(self.serializer_class(data, many=True).data, response.data['results'])

        # for poll that has no choices
        user = self.users[1]
        poll = models.Poll.objects.filter(created_by=user)[0]
        response = self.get_response('get', poll)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertListEqual([], response.data['results'])

        # for poll that is not exist
        data = {'id': 0}
        poll = models.Poll.objects.filter(**data)
        self.assertEqual(0, len(poll))
        response = self.get_response('get', data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        test_content = b'{"non_field_errors":["Poll 0 does not exists"]}'
        self.assertEqual(test_content, response.content)


class TestChoiceDetail(ChoiceMixin, APITestCase):

    # path("poll/<int:pk>/choice/<int:choice_pk>/", views.ChoiceDetail.as_view(), name="choice_detail"),
    view_name = 'pollsapi:choice_detail'
    view_name_kwargs_map = {'pk': 'poll_id', 'choice_pk': 'id'}

    def get_token_login_url_params(self):
        return self.dummy_choice

    def test_perform_token_login(self):
        self.dummy_choice = self.create_fixtures()[0]
        super().test_perform_token_login()

    def test_perform_detail(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)
        choice = fix_data[0]

        # test choice where pol is not exist
        url_params = {'poll_id': 0, 'id': choice.pk}
        choice = models.Choice.objects.filter(**url_params)
        self.assertEqual(0, len(choice))
        response = self.get_response('get', url_params)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        test_content = b'{"non_field_errors":["Poll 0 does not exists"]}'
        self.assertEqual(test_content, response.content)

        # test two users (logged and no)
        # no logged
        resp = self.get_response('get', fix_data[0])
        self.assertDictEqual(resp.data, self.serializer_class(fix_data[0]).data)

        user = self.users[0]
        #logged
        resp = self.get_response('get', fix_data[0], HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertDictEqual(resp.data, self.serializer_class(fix_data[0]).data)

        islogged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(islogged)
        resp = self.get_response('get', fix_data[0])
        self.assertDictEqual(resp.data, self.serializer_class(fix_data[0]).data)

    def test_perform_edit(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)

        user = self.users[1]

        # test two users (logged and no)
        # logged - unsuccessful for does not owned
        new_data = {'choice_text': f'modified_by_user{user.pk}'}
        resp = self.get_response('put', fix_data[0], data=new_data, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
        test_resp_content = b'{"detail":"You do not have permission to perform this action."}'
        self.assertEqual(test_resp_content, resp.content)

        # no logged - unsuccessful
        resp = self.get_response('put', fix_data[0], data=new_data)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)
        test_resp_content = b'{"detail":"Authentication credentials were not provided."}'
        self.assertEqual(test_resp_content, resp.content)

        # logged - successful for owned poll
        user = self.users[2]
        choice = fix_data[-1]
        self.assertEqual(user, choice.poll.created_by)

        for method in ('put', 'patch'):
            with self.subTest(method=method):
                new_data = {'choice_text': f'{method}: modified_by_{user.username}_id[{user.pk}] for poll[{choice.poll_id}]'}
                self.assertNotEqual(new_data['choice_text'], choice.choice_text)

                resp = self.get_response(
                    method, choice,
                    data=new_data,
                    HTTP_AUTHORIZATION=f'Token {user.auth_token.key}'
                )
                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                self.assertDictEqual(
                    dict(self.serializer_class(choice).data) | new_data,
                    dict(resp.data)
                )

    def test_perform_delete(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)

        user = self.users[1]
        # test two users (logged and no)
        # no logged - unsuccessful
        resp = self.get_response('delete', fix_data[0])
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

        # logged - unsuccessful for does not owned
        resp = self.get_response('delete', fix_data[0], HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # logged - successful for owned poll
        choice = fix_data[-1]
        user = self.users[2]

        qs = models.Choice.objects.filter(pk=choice.pk, poll=choice.poll_id)
        self.assertEqual(1, len(qs))

        resp = self.get_response('delete', choice, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)

        qs = self.serializer_class.Meta.model.objects.filter(pk=choice.pk, poll=choice.poll_id)
        self.assertEqual(0, len(qs))
