# IDE: PyCharm
# Project: drf
# Path: ${DIR_PATH}
# File: ${FILE_NAME}
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-13 (y-m-d) 7:33 AM

import json
from rest_framework.test import APITestCase
import requests
from django.contrib.auth.models import User

from rest_framework.renderers import JSONRenderer

from tutorial.snippets.models import Snippet
from tutorial.snippets.serializers import SnippetSerializer, SnippetModelSerializer


raise NotImplementedError('Cause - It is not worth of spending time on testing all of the cases in the tutorial')


class TestSnippetSerializer(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', password='12345678', email='test@test.io')

    def test_all(self):
        Snippet.objects.all().delete()

        snipopts = [
            {'code': 'foo = "bar"\n',           'id': None, 'snippet': None, 'serializer': None},
            {'code': 'print("hello, world")\n', 'id': None, 'snippet': None, 'serializer': None},
        ]

        for opt in snipopts:
            opt['snippet'] = snippet = Snippet(code=opt['code'], owner=self.user)
            snippet.save()

            self.assertIsNotNone(snippet.id)
            opt['id'] = snippet.id

            snippet.refresh_from_db()
            self.assertEqual(opt['code'], snippet.code)

        self.assertEqual(2, Snippet.objects.count())

        for opt in snipopts:
            opt['serializer'] = serializer = SnippetSerializer(opt['snippet'])
            res = {'id': opt['id'], 'title': '', 'code': opt['code'], 'linenos': False, 'language': 'python', 'style': 'friendly'}
            self.assertDictEqual(res, serializer.data)

            content = JSONRenderer().render(serializer.data)
            content_dict = json.loads(content.decode())
            self.assertDictEqual(res, content_dict)

        # update
        snip_obj = Snippet.objects.get(pk=snipopts[1]['id'])
        mcode = 'print("MoDiFiEd - hello, world")'  # trailing \n is lost during validation
        ser = SnippetSerializer(snip_obj, {'code': mcode}, partial=True)
        self.assertTrue(ser.is_valid())
        ser.save()

        snip_obj.refresh_from_db()
        self.assertEqual(snip_obj.code, mcode)

        # create
        ncode = 'foo = "bar"\n some_assignment = "cvxczvzxcvzxc"'
        new = {
            'title': 'some title',
            'code': ncode,
            'linenos': False,
            'language': 'python',
            'style': 'friendly',
            'owner': self.user.pk,
        }
        ser = SnippetSerializer(data=new)
        self.assertTrue(ser.is_valid())
        ser.save()

        self.assertEqual(3, Snippet.objects.count())
        for fname, val in new.items():
            inst_val = getattr(ser.instance, fname)
            if isinstance(inst_val, User):
                inst_val = inst_val.pk
            self.assertEqual(val, inst_val)

        # create SnippetModelSerializer()
        ncode = 'foo = "bar"\n some_assignment = "cvxczvzxcvzxc"'
        new = {
            'title': 'some title for model serializer',
            'code': ncode,
            'linenos': False,
            'language': 'python',
            'style': 'friendly',
            'owner': self.user
        }
        ser = SnippetModelSerializer(data=new)
        self.assertTrue(ser.is_valid())
        ser.save()

        self.assertEqual(4, Snippet.objects.count())
        for fname, val in new.items():
            self.assertEqual(val, getattr(ser.instance, fname))

    def test_snippet_list(self):
        url = 'http://127.0.0.1:8000/snippets/'
        ncode = 'foo = "bar"\n some_assignment = "cvxczvzxcvzxc"'
        new = {'title': 'some title', 'code': ncode, 'linenos': False, 'language': 'python', 'style': 'friendly'}

        r = requests.get(url)
        data = r.json()
        self.assertIsInstance(data, list)

        r = requests.post(url, json=new)
        self.assertEqual(201, r.status_code)

        r_json = r.json()
        new['id'] = r_json['id']
        self.assertDictEqual(new, r_json)

        new['language'] = None
        r = requests.post(url, json=new)
        self.assertEqual(400, r.status_code)
        self.assertDictEqual({'language': ['This field may not be null.']}, r.json())

    def test_snippet_detail(self):
        ...
