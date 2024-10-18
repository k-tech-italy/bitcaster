import json
from typing import Any

from django.http import HttpRequest
from django.db.models import QuerySet
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from mypy.dmypy.client import action
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from ..auth.constants import Grant
from ..models import Channel, Organization, Project
from .base import SecurityMixin
from .serializers import ChannelSerializer


app_name = "api"


class ChannelView(SecurityMixin, ViewSet, ListAPIView, RetrieveAPIView, CreateAPIView):
    """
    List channels.
    """

    serializer_class = ChannelSerializer
    required_grants = [Grant.ORGANIZATION_READ]

    def get_queryset(self) -> QuerySet[Channel]:
        if "prj" in self.kwargs:
            return Channel.objects.filter(
                organization__slug=self.kwargs["org"],
                project__slug=self.kwargs["prj"],
            )

        elif "org" in self.kwargs:
            return Channel.objects.filter(
                organization__slug=self.kwargs["org"],
            )

    @extend_schema(description=_("List organization channels"))
    def list_for_org(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(description=_("List Project channels"))
    def list_for_project(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(description=_("Create a channel"))
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        print(request.data)

        if kwargs.get('prj'):
            prj_id = Project.objects.get(name = kwargs.get("prj")).id
            request.data["project"] = prj_id

        org_id = Organization.objects.get(name = kwargs.get("org")).id

        request.data["organization"] = org_id
        print(request.data)


        serializer = ChannelSerializer(data=request.data)


        from rest_framework import status
        if serializer.is_valid():
            instance = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)
        # print(serializer.fields)
        # print(request.data)
        # print(args)
        # print(kwargs)
        # return post(request, *args, **kwargs)

