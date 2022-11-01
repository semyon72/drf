# IDE: PyCharm
# Project: drf
# Path: tutorial/snippets
# File: permissions.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-18 (y-m-d) 7:08 PM
from rest_framework import permissions
from rest_framework.request import Request

from tutorial.snippets.models import Snippet


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request: Request, view, obj: Snippet):

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user == obj.owner

