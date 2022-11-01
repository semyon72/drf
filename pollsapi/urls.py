# IDE: PyCharm
# Project: drf
# Path: pollsapi
# File: urls.py
# Contact: Semyon Mamonov <semyon.mamonov@gmail.com>
# Created by ox23 at 2022-09-21 (y-m-d) 5:58 AM

# inspired by tutorial
# https://books.agiliq.com/projects/django-api-polls-tutorial/en/latest/introduction.html
# but along with fixes and complete tests


from django.urls import path

from pollsapi import views
from rest_framework.schemas import get_schema_view

app_name = 'pollsapi'

urlpatterns = [
    # path('', views.ApiRootView.as_view(), name='api_root'),
    path('user/', views.UserCreate.as_view(), name='user_create'),
    path('login/', views.Login.as_view(), name='login'),
    path('poll/', views.PollList.as_view(), name='poll_list'),
    path('poll/<int:pk>/', views.PollDetail.as_view(), name='poll_detail'),
    path("poll/<int:pk>/choice/", views.ChoiceList.as_view(), name="choice_list"),
    path("poll/<int:pk>/choice/<int:choice_pk>/", views.ChoiceDetail.as_view(), name="choice_detail"),

    path("poll/<int:pk>/choice/<int:choice_pk>/vote/", views.Vote.as_view(), name="vote"),
]
