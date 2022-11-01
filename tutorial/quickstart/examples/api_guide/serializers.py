# IDE: PyCharm
# Project: tutorial
# Path: quickstart/examples/api_guide
# File: serializers.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-06 (y-m-d) 7:54 AM


from datetime import datetime

import rest_framework.serializers as drf_serial
import rest_framework.fields as drf_fields


class Comment:

    def __init__(self, email: str, content: str, created: datetime = None) -> None:
        self.email: str = email
        self.content: str = content
        self.created: datetime = created or datetime.now()


class CommentSerializer(drf_serial.Serializer):

    email: drf_fields.EmailField = drf_fields.EmailField(help_text='Your email')
    content: drf_fields.CharField = drf_fields.CharField(help_text='Your content of comment')
    created: drf_fields.DateTimeField = drf_fields.DateTimeField(help_text='Date + time of comment was created')

    def update(self, instance, validated_data):
        instance.__dict__.update(validated_data)
        return instance

    def create(self, validated_data):
        inst = Comment(**validated_data)
        return inst


if __name__ == '__main__':

    import sys
    import os
    import django

    # https://docs.djangoproject.com/en/4.1/topics/settings/#either-configure-or-django-settings-module-is-required
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
    sys.path.insert(0, '/home/ox23/PycharmProjects/drf/')
    django.setup()

    cmnt = Comment('test@jj.com', 'tru-lala and tra-lala')

    cmnt_ser = CommentSerializer(cmnt)
    print('## CommentSerializer(cmnt).data:', f'{cmnt_ser.data}')

    cmnt_ser = CommentSerializer(data=cmnt.__dict__)
    print('## Valid CommentSerializer(data=cmnt.__dict__)')
    if cmnt_ser.is_valid():
        print(f'\t.errors: {cmnt_ser.errors}')
        print('\t.initial_data', cmnt_ser.initial_data)
        print('\t.data:', f'{cmnt_ser.data}')
        print('\t.validated_data:', f'{cmnt_ser.validated_data}')

    cmnt = Comment('test.jj.com', 'tru-lala and tra-lala')
    cmnt_ser = CommentSerializer(data=cmnt.__dict__)
    print('## Not valid CommentSerializer(data=cmnt.__dict__)')
    if not cmnt_ser.is_valid():
        print(f'\t.errors: {cmnt_ser.errors}')
        print('\t.initial_data', cmnt_ser.initial_data)
        print('\t.data:', f'{cmnt_ser.data}')
        print('\t.validated_data:', f'{cmnt_ser.validated_data}')

    cmnt = Comment('test.jj.com', 'tru-lala and tra-lala')
    data = {'email': 'test@yoyoy.com', 'content': 'MODIFIED - tru-lala and tra-lala'}
    cmnt_ser = CommentSerializer(cmnt, data=data, partial=True)
    print('## Valid CommentSerializer(cmnt, data=data, partial=True)')
    if cmnt_ser.is_valid():
        print(f'\t.errors: {cmnt_ser.errors}')
        print('\t.initial_data', cmnt_ser.initial_data)
        print('\t.data:', f'{cmnt_ser.data}')
        print('\t.validated_data:', f'{cmnt_ser.validated_data}')

    print(f'\tcmnt: {cmnt}: {vars(cmnt)}')
    cmnt_ser = CommentSerializer(cmnt, data=data, partial=True)
    if cmnt_ser.is_valid():
        cmnt_ser.save()
    print(f'\tcmnt after cmnt_ser.save() [update]: {cmnt}: {vars(cmnt)}')

    print('## Valid CommentSerializer(data=data) to create')
    data = {'email': 'test@aiyaa.com', 'content': 'NEW - tra-lala and tru-lala', 'created': datetime.now()}
    cmnt_ser = CommentSerializer(data=data)
    cmnt = None
    if cmnt_ser.is_valid():
        cmnt = cmnt_ser.save()
    print(f'\tnew instance after cmnt_ser.save() [create]: {cmnt}: {vars(cmnt)}')



