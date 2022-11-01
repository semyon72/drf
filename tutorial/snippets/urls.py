# IDE: PyCharm
# Project: drf
# Path: tutorial/snippets
# File: urls.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-16 (y-m-d) 11:27 AM
from django.urls import path, include
from rest_framework import renderers
from rest_framework.routers import DefaultRouter

from tutorial.snippets import views

router = DefaultRouter()
router.register('snippets', views.SnippetViewSet)
router.register('users', views.UserViewSet)

app_name = 'snippets'

urlpatterns = [
    *router.urls
]
