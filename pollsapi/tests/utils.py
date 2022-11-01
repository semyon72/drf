# IDE: PyCharm
# Project: drf
# Path: pollsapi/tests
# File: utils.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-10-06 (y-m-d) 5:51 PM

from typing import Optional

from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


class ClientToolMixin:
    # url_pattern something like
    # '/api-polls/poll/' - list, create
    # '/api-polls/poll/{pk}/' - get, put, patch, delete
    view_name: str = None
    # view_name_kwargs_map is dict of url_key: attr_name, example {'pk': 'pk'} or {'pk': 'id'} last is better
    # because serialized data will contain 'id' key
    view_name_kwargs_map: dict = None
    serializer_class = None

    password = '12345678'
    client = APIClient()
    users: list[Optional[User]] = None

    def setUp(self) -> None:
        assert isinstance(self.view_name, str), '"view_name" is not str. It must be something like "polls:poll_list"'
        assert issubclass(self.serializer_class, Serializer),\
            f'"serializer_class" is not subclass of {type(Serializer).__module__}.{type(Serializer).__name__}'

        self.users = []
        for i in range(3):
            credentials = {'username': f'test{i}', 'password': self.password}
            user = User.objects.create_user(**credentials)
            Token.objects.create(user=user)
            self.users.append(user)

    def extract_by_map(self, d: dict) -> dict:
        result = {}
        if d is None:
            return result

        assert isinstance(d, dict), 'parameter "d" must be dict or None'

        for url_key, dict_key in self.view_name_kwargs_map.items():
            try:
                val = d[dict_key]
            except KeyError as exc:
                raise KeyError(f'Map has mapping [{url_key}->{dict_key}] that has not entry in {d}') from exc

            result[url_key] = val
        return result

    def get_url(self, args=None, kwargs=None, **extra):
        kwargs = {
            'viewname': self.view_name,
            'args': args,
            'kwargs': kwargs
        }
        kwargs.update(extra)
        return reverse(**kwargs)

    def get_url_kwargs(self, params) -> dict:
        if params is None:
            return {}

        result = {}
        if not isinstance(params, dict):
            sentinel = object()
            for url_key, attr_name in self.view_name_kwargs_map.items():
                val = getattr(params, attr_name, sentinel)
                if val is sentinel:
                    raise AttributeError(
                        f'Map has mapping [{url_key}->{attr_name}] but object {params} has no {attr_name} attribute'
                    )
                result[attr_name] = val
        else:
            result = params

        return self.extract_by_map(result)

    def get_response(self, method, url_params=None, data: dict = None, **extra) -> Response:
        try:
            method_handler = getattr(self.client, method.lower())
        except KeyError as exc:
            raise AssertionError(f'client does not support method "{method}"') from exc
        assert callable(method_handler), f'client has method "{method}" but it is not callable'

        # method_handler_signature(path, data = None, format=None .....)
        kwargs = {
            'path': self.get_url(kwargs=self.get_url_kwargs(url_params)),
            'data': data
        }
        kwargs.update(extra)
        return method_handler(**kwargs)

    def check_response_single_object(self, response, queryset=None):
        """
        Tests len(queryset) == 1, response.data == serialize(queryset[0]),
        does queryset.delete() and tests len(queryset)==0
        useful for post, put, patch actions
        """
        if queryset is None:
            queryset = self.serializer_class.Meta.model.objects.all()
        self.assertEqual(1, len(queryset))
        ser = self.serializer_class(queryset[0])
        resp_dict = dict(response.data)
        self.assertDictEqual(dict(ser.data), resp_dict)

        queryset.delete()
        self.assertEqual(0, queryset.model.objects.count())

    def test_perform_session_login(self):
        user = self.users[0]

        is_logged = self.client.login(username=user.username, password='fake_pass')
        self.assertFalse(is_logged)

        is_logged = self.client.login(username=user.username, password=self.password)
        self.assertTrue(is_logged)

    def get_token_login_url_params(self):
        raise NotImplementedError(
            'if .view_name is not parameterized then just need to return None or {}. '
            'Otherwise, it should return object with attributes that maps by .view_name_kwargs_map. '
            'Same, if returned dict, but instead name of attributes will be used key of dictionary.'
        )

    def test_perform_token_login(self):
        """
        Tests Token authentication
        """
        user = self.users[0]
        resp = self.get_response(
            'get',
            self.get_token_login_url_params(),
            HTTP_AUTHORIZATION='Token fake_token'
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, resp.status_code)

        resp = self.get_response(
            'get',
            self.get_token_login_url_params(),
            HTTP_AUTHORIZATION='Token {}'.format(user.auth_token.key)
        )
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(resp.renderer_context['request'].user, user)

