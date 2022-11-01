# IDE: PyCharm
# Project: drf
# Path: tutorial/snippets
# File: serializers.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-11 (y-m-d) 11:04 AM

from django.db.models import Model
from django.contrib.auth.models import User, AnonymousUser

from rest_framework import serializers
from rest_framework.settings import api_settings
from rest_framework.exceptions import ValidationError

from tutorial.snippets.models import LANGUAGE_CHOICES, STYLE_CHOICES, Snippet

# implementation of
# https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/
#
#     Code snippets are always associated with a creator.
#     Only authenticated users may create snippets.
#     Only the creator of a snippet may update or delete it.
#     Unauthenticated requests should have full read-only access.


class SnippetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=True, allow_blank=True, max_length=100)
    code = serializers.CharField(style={'base_template': 'textarea.html'})
    linenos = serializers.BooleanField(default=False)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default='python')
    style = serializers.ChoiceField(choices=STYLE_CHOICES, default='friendly')
    owner = serializers.ReadOnlyField(source='owner.username')

    def create(self, validated_data):
        owner = self.context['request'].user
        if isinstance(AnonymousUser, owner):
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: ['User should be authenticated. Anonymous is gotten.']
            }, code='not_a_list')

        validated_data['owner'] = owner
        return Snippet.objects.create(**validated_data)

    def update(self, instance: Snippet, validated_data):
        cowner: User = self.context['request'].user
        if instance.owner != cowner:
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [
                    f'Only owner "{instance.owner.username}" can modify. But logged user is {cowner.username}'
                ]
            }, code='not_a_list')

        for field_name, val in validated_data.items():
            f: serializers.Field = self.fields.get(field_name)
            if f is not None and not f.read_only:
                setattr(instance, field_name, val)

        instance.save()
        return instance


class UserModelSerializer(serializers.HyperlinkedModelSerializer):
    snippets = serializers.HyperlinkedRelatedField(many=True, view_name='snippets:snippet-detail', read_only=True)

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'snippets']
        extra_kwargs = {
            'url': {'view_name': 'snippets:user-detail'}
        }


class SnippetModelSerializer(serializers.HyperlinkedModelSerializer):

    owner = serializers.ReadOnlyField(source='owner.username')
    highlight = serializers.HyperlinkedIdentityField(view_name='snippets:snippet-highlight', format='html')

    class Meta:
        model = Snippet
        fields = '__all__'  # ['url', 'id', 'highlight', 'owner', 'title', 'code', 'linenos', 'language', 'style']
        extra_kwargs = {
            'url': {'view_name': 'snippets:snippet-detail'}
        }
