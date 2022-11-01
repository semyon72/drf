from django.contrib.auth.models import User
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, permissions, renderers
from rest_framework.decorators import api_view, action
from rest_framework.parsers import JSONParser
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.reverse import reverse

from tutorial.snippets.models import Snippet
from tutorial.snippets.permissions import IsOwnerOrReadOnly
from tutorial.snippets.serializers import SnippetSerializer, SnippetModelSerializer, UserModelSerializer
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.mixins import ( CreateModelMixin, DestroyModelMixin, ListModelMixin,
                                    RetrieveModelMixin, UpdateModelMixin)
from rest_framework import generics
from rest_framework import viewsets


@api_view(['GET', 'POST'])
def snippet_list(request):

    if request.method == 'GET':
        # list of all
        snippets = Snippet.objects.all()
        ser = SnippetSerializer(snippets, many=True)
        return Response(ser.data)

    if request.method == 'POST':
        # create new one snippet
        data = JSONParser().parse(request)
        ser = SnippetSerializer(data=data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def snippet_detail(request, pk):

    try:
        snip = Snippet.objects.get(pk=pk)
    except Snippet.DoesNotExist as exc:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        ser = SnippetSerializer(snip)
        return Response(ser.data)

    if request.method == 'PUT':
        data = JSONParser().parse(request)
        ser = SnippetSerializer(snip, data=data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return JsonResponse(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        snip.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class SnippetCreateList(ListModelMixin, CreateModelMixin, generics.GenericAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class SnippetRetrieveUpdateDelete(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, generics.GenericAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer

    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class SnippetCreateListConcise(generics.ListCreateAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SnippetRetrieveUpdateDeleteConcise(generics.RetrieveUpdateDestroyAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class UserListConcise(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer


class UserDetailConcise(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer


@api_view(['GET'])
def api_root(request, format=None):
    return Response(
        {
            'users': reverse('snippets:user_list', request=request, format=format),
            'snippets': reverse('snippets:snippet_list', request=request, format=format)
        }
    )


class SnippetHighlight(generics.GenericAPIView):
    queryset = Snippet.objects.all()
    renderer_classes = [renderers.StaticHTMLRenderer]

    def get(self, request, pk):
        obj = self.get_object()
        return Response(obj.highlighted)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer


class SnippetViewSet(viewsets.ModelViewSet):
    queryset = Snippet.objects.all()
    serializer_class = SnippetModelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @action(['GET'], detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def highlight(self, request, *args, **kwargs):
        """
            Some function description - SnippetViewSet.highlight
        """
        obj = self.get_object()
        return Response(obj.highlighted)

