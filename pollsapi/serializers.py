# IDE: PyCharm
# Project: drf
# Path: pollsapi
# File: serializers.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-21 (y-m-d) 6:44 AM
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from pollsapi import models


class VoteSerializer(serializers.ModelSerializer):
    voted_by = serializers.PrimaryKeyRelatedField(read_only=True, source='voted_by.username')

    class Meta:
        model = models.Vote
        fields = '__all__'
        read_only_fields = ['poll', 'choice']


class ChoiceSerializer(serializers.ModelSerializer):
    votes = VoteSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = models.Choice
        fields = '__all__'
        read_only_fields = ['poll']


class PollSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = models.Poll
        fields = '__all__'
        read_only_fields = ['created_by']


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        obj = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password')
        )
        return obj


class LoginSerializer(serializers.ModelSerializer):
    token = serializers.ReadOnlyField(source='auth_token.key')

    class Meta:
        model = User
        fields = ['username', 'token', 'password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super().build_standard_field(field_name, model_field)
        # remove user exists validator
        if field_name == 'username':
            validators = field_kwargs.get('validators', [])
            if validators:
                unique = [v for v in validators if isinstance(v, UniqueValidator)]
                assert len(unique) <= 1, 'Unsupported case User has more than one UniqueValidator'
                if unique:
                    validators.remove(unique[0])

        return field_class, field_kwargs

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(self.context.get('request'), username=username, password=password)
        if user is not None:
            assert isinstance(user, self.Meta.model),\
                f'class Meta.model attribute should be type of {type(user).__name__}'
            self.instance = user
        else:
            raise ValidationError('Authentication error')
        return attrs

    def create(self, validated_data) -> User:
        return self.instance

    def update(self, instance, validated_data) -> User:
        # stub for not appropriate external usage
        return instance
