"""tutorial URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.documentation import include_docs_urls

api_polls_path_prefix = 'api-polls/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    # path('api-comment/', include('comment.urls')),
    path('api-snippets/', include('tutorial.snippets.urls')),
    path('', RedirectView.as_view(url='/%s' % api_polls_path_prefix)),
    path(api_polls_path_prefix, include('pollsapi.urls')),
    path(api_polls_path_prefix,
         include_docs_urls(
             title='Polls API',
             urlconf='pollsapi.urls',
             schema_url='/%s' % api_polls_path_prefix,
             permission_classes=[]
         )),

]
