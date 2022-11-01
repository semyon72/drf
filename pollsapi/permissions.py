# IDE: PyCharm
# Project: drf
# Path: pollsapi
# File: permissions.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-23 (y-m-d) 11:25 AM

from rest_framework import permissions
from pollsapi import models


class PollsChoiceIsOwnerOrStaff(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, (models.Poll, models.Choice)):
            if request.user.is_staff:
                return True

            poll = obj
            if isinstance(obj, models.Choice):
                poll = obj.poll

            return poll.created_by_id == request.user.pk
