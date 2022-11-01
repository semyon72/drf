# IDE: PyCharm
# Project: drf
# Path: ${DIR_PATH}
# File: ${FILE_NAME}
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-02 (y-m-d) 10:57 AM

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from pollsapi import models, serializers
from pollsapi.tests.utils import ClientToolMixin


class PollMixin(ClientToolMixin):
    serializer_class = serializers.PollSerializer

    def create_fixtures(self) -> list[serializers.PollSerializer]:
        """
        It will create 3 polls 0 - for self.users[0], 1 - for self.users[1] and 2 - for self.users[2]
        It does not test authentication
        """
        results = []
        for i, user in enumerate(self.users):
            if i == 0:
                continue
            for j in range(1, i+1):
                question = f'question_{user.username}_{j}]'
                data = {'question': question, 'created_by': user}
                instance = self.serializer_class.Meta.model.objects.create(**data)
                ser = self.serializer_class(instance)
                results.append(ser.data)

        return results


class TestPollList(PollMixin, APITestCase):
    """
        It does not test authentication process
    """
    view_name = 'pollsapi:poll_list'

    def get_token_login_url_params(self):
        return None

    def test_perform_create(self):
        # test not authenticated - fail
        data = {'question': 'test_question'}
        resp: Response = self.get_response('post', data=data)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)
        self.assertEqual(0, models.Poll.objects.count())

        user = self.users[0]

        # test token authenticated creation - good
        resp = self.get_response('post', data=data, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        self.check_response_single_object(resp)

        # test session authenticated creation - good
        islogged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(islogged)

        resp = self.get_response('post', data=data)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)

        self.check_response_single_object(resp)

    def test_perform_list(self):
        data = self.create_fixtures()
        self.assertEqual(3, len(data))

        response = self.get_response('get')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertListEqual(data, response.data['results'])


class TestPollDetail(PollMixin, APITestCase):
    """
        It does not test authentication process
    """
    view_name = 'pollsapi:poll_detail'
    view_name_kwargs_map = {'pk': 'id'}

    def get_token_login_url_params(self):
        return self.dummy_poll

    def test_perform_token_login(self):
        user = self.users[0]
        self.dummy_poll = self.serializer_class.Meta.model.objects.create(question='dummy_question', created_by=user)
        super().test_perform_token_login()
        self.dummy_poll.delete()

    def test_perform_detail(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)

        # test two users (logged and no)
        # no logged
        resp = self.get_response('get', fix_data[0])
        self.assertDictEqual(dict(resp.data), fix_data[0])

        user = self.users[0]
        #logged
        resp = self.get_response('get', fix_data[0], HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertDictEqual(dict(resp.data), fix_data[0])

        islogged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(islogged)
        resp = self.get_response('get', {'id': fix_data[0]['id']})
        self.assertDictEqual(dict(resp.data), fix_data[0])

    def test_perform_edit(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)

        user = self.users[0]

        # test two users (logged and no)
        # logged - unsuccessful for does not owned
        new_data = {'question': f'modified_by_user{user.pk}'}
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
        poll_data = dict(fix_data[-1])
        user = [user for user in self.users if user.id == poll_data['created_by']]
        self.assertEqual(1, len(user), f'has no appropriate user in {self.users} for data {poll_data}')
        user = user[0]

        for method in ('put', 'patch'):
            with self.subTest(method=method):
                new_data = {'question': f'{method}: modified_by_{user.username}_id[{user.pk}]'}
                self.assertNotEqual(new_data['question'], poll_data['question'])

                resp = self.get_response(
                    method, poll_data,
                    data=new_data,
                    HTTP_AUTHORIZATION=f'Token {user.auth_token.key}'
                )
                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                self.assertDictEqual(poll_data | new_data | {'pub_date': resp.data['pub_date']}, dict(resp.data))

    def test_perform_delete(self):
        fix_data = self.create_fixtures()
        self.assertGreater(len(fix_data), 0)

        user = self.users[0]
        # test two users (logged and no)
        # no logged - unsuccessful
        resp = self.get_response('delete', fix_data[0])
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

        # logged - unsuccessful for does not owned
        resp = self.get_response('delete', fix_data[0], HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # logged - successful for owned poll
        poll_data = dict(fix_data[-1])
        user = [user for user in self.users if user.id == poll_data['created_by']]
        self.assertEqual(1, len(user), f'has no appropriate user in {self.users} for data {poll_data}')
        user = user[0]

        qs = self.serializer_class.Meta.model.objects.filter(pk=poll_data['id'])
        self.assertEqual(1, len(qs))

        resp = self.get_response('delete', poll_data, HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        self.assertEqual(status.HTTP_204_NO_CONTENT, resp.status_code)

        qs = self.serializer_class.Meta.model.objects.filter(pk=poll_data['id'])
        self.assertEqual(0, len(qs))
