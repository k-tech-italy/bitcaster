from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from .base import BaseView
from ..auth.constants import Grant
from ..models import Application, DistributionList, User


class ApplicationUnsubscribeView(BaseView):
    """Unsubscribe a User from the distribution lists pinned to the Application in the URL path."""

    required_grants = [Grant.MANAGE_APPLICATION_USERS]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="ApplicationUnsubscribeResponse", fields={"deleted": serializers.IntegerField()}
            )
        },
        description=_(
            "Unsubscribe a user from the application: removes the user's assignments from all "
            "distribution lists pinned to the application. "
            "Returns the number of removed distribution list entries."
        ),
    )
    def post(self, request: Request, org: str, prj: str, app: str, username: str) -> Response:
        application = get_object_or_404(Application, slug=app, project__slug=prj, project__organization__slug=org)
        user = get_object_or_404(User, username=username, roles__organization=application.project.organization)

        through_model = DistributionList.recipients.through
        deleted, _ = through_model.objects.filter(
            distributionlist__application=application,
            assignment__address__user=user,
        ).delete()

        return Response({"deleted": deleted})
