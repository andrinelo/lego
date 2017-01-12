from rest_framework import decorators, status, viewsets
from rest_framework.response import Response

from lego.apps.meetings.models import Meeting, MeetingInvitation
from lego.apps.meetings.permissions import MeetingInvitationPermissions, MeetingPermissions
from lego.apps.meetings.serializers import (MeetingBulkInvite, MeetingGroupInvite,
                                            MeetingInvitationSerializer,
                                            MeetingInvitationUpdateSerializer, MeetingSerializer,
                                            MeetingUserInvite)
from lego.apps.permissions.views import AllowedPermissionsMixin


class MeetingViewSet(AllowedPermissionsMixin, viewsets.ModelViewSet):
    queryset = Meeting.objects.prefetch_related('invitations', 'invitations__user')
    permission_classes = (MeetingPermissions,)
    serializer_class = MeetingSerializer

    @decorators.detail_route(methods=['POST'], serializer_class=MeetingUserInvite)
    def invite_user(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        meeting.invite_user(user)
        return Response(data='Invited user ' + str(user.id), status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['POST'], serializer_class=MeetingBulkInvite)
    def bulk_invite(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.validated_data['users']
        groups = serializer.validated_data['groups']
        if not len(users) and not len(groups):
            return Response(data='No users or groups given', status=status.HTTP_400_BAD_REQUEST)
        for user in users:
            meeting.invite_user(user)
        for group in groups:
            meeting.invite_group(group)
        return Response(data='Invited users {}, and groups {}'.format(users, groups),
                        status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['POST'], serializer_class=MeetingGroupInvite)
    def invite_group(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data['group']
        meeting.invite_group(group)
        return Response(data='Invited group ' + str(group.id), status=status.HTTP_200_OK)


class MeetingInvitationViewSet(AllowedPermissionsMixin, viewsets.ModelViewSet):
    queryset = MeetingInvitation.objects.select_related('user')
    permission_classes = (MeetingInvitationPermissions,)
    lookup_field = 'user__id'

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return MeetingInvitationUpdateSerializer
        return MeetingInvitationSerializer

    def get_queryset(self):
        return MeetingInvitation.objects.filter(meeting=self.kwargs['meeting_pk'])
