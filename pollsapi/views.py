# Create your views here.

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.authtoken.models import Token

from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.relations import PrimaryKeyRelatedField

from rest_framework.settings import api_settings
from rest_framework import generics, views, permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse

from pollsapi import models, serializers
from pollsapi.permissions import PollsChoiceIsOwnerOrStaff


class PollBaseMixin:
    queryset = models.Poll.objects.prefetch_related('choices__votes').all()
    serializer_class = serializers.PollSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, PollsChoiceIsOwnerOrStaff]


class PollList(PollBaseMixin, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PollDetail(PollBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    pass


class ChoiceBaseMixin:
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, PollsChoiceIsOwnerOrStaff]
    serializer_class = serializers.ChoiceSerializer
    _poll: models.Poll = None

    def get_poll(self):
        if self._poll is None:
            poll_id = self.kwargs['pk']
            try:
                self._poll = models.Poll.objects.get(pk=poll_id)
            except models.Poll.DoesNotExist as exc:
                raise ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [f'Poll {poll_id} does not exists']
                })

        return self._poll

    def get_queryset(self):
        poll = self.get_poll()
        return super().get_queryset().filter(poll=poll)


class ChoiceList(ChoiceBaseMixin, generics.ListCreateAPIView):
    queryset = models.Choice.objects.prefetch_related('votes').select_related('poll')

    def perform_create(self, serializer):
        poll = self.get_poll()
        if poll.created_by_id != self.request.user.pk:
            raise PermissionDenied('You can not create choice for this poll')
        serializer.save(poll=self._poll)


class ChoiceDetail(ChoiceBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'choice_pk'
    queryset = models.Choice.objects.select_related('poll').all()


class Vote(generics.CreateAPIView):

    serializer_class = serializers.VoteSerializer
    queryset = serializer_class.Meta.model.objects.all()

    def validate_poll_choice(self, serializer: serializers.VoteSerializer) -> models.Choice:
        choice_id = self.kwargs.get('choice_pk')
        choice_fld: PrimaryKeyRelatedField = serializer.fields['choice']

        try:
            if isinstance(choice_id, bool):
                raise TypeError
            choice_qs = models.Choice.objects.select_related('poll')
            choice = choice_qs.get(pk=choice_id)
        except ObjectDoesNotExist:
            choice_fld.fail('does_not_exist', pk_value=choice_id)
        except (TypeError, ValueError):
            choice_fld.fail('incorrect_type', data_type=type(choice_id).__name__)

        poll_id = self.kwargs.get('pk')
        poll = choice.poll

        poll_fld: PrimaryKeyRelatedField = serializer.fields['poll']
        try:
            poll_id = type(choice.poll.pk)(poll_id)
        except (TypeError, ValueError):
            poll_fld.fail('incorrect_type', data_type=type(poll_id).__name__)

        if poll_id != poll.pk:
            # none_field_error
            raise ValidationError(['The choice is not appropriate for a poll\'s question'])

        return poll, choice

    def perform_create(self, serializer: serializers.VoteSerializer):
        # add automatically poll, choice and user objects

        try:
            poll, choice = self.validate_poll_choice(serializer)
        except ValidationError as exc:
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: exc.detail})

        errors = {}
        user = self.request.user
        if not user.is_authenticated:
            errors.setdefault('user', []).append('Allowed only authenticated users')

        if poll.votes.filter(voted_by=user).exists():
            errors.setdefault(api_settings.NON_FIELD_ERRORS_KEY, []).append(
                'You are voted on this poll'
            )

        if errors:
            raise ValidationError(errors)

        serializer.save(poll=poll, choice=choice, voted_by=user)


class UserCreate(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.UserSerializer

    def perform_create(self, serializer):
        # need to create a user, before create a token
        instance = serializer.save()
        Token.objects.create(user=instance)


class Login(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.LoginSerializer


class ApiRootView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({
            'poll list': reverse('pollsapi:poll_list', request=request),
            'poll detail': 'poll/<int:pk>/',
            'choices for poll': 'poll/<int:pk>/choice/',
            'vote': 'poll/<int:pk>/choice/<int:choice_pk>/vote/',
        })

