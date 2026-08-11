from typing import TYPE_CHECKING

import logging

from adminfilters.autocomplete import AutoCompleteFilter

from bitcaster.models import ApplicationMembership

from .base import BaseAdmin

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class ApplicationMembershipAdmin(BaseAdmin[ApplicationMembership]):
    list_display = (
        "user",
        "application",
    )
    list_filter = (
        ("user", AutoCompleteFilter),
        ("application", AutoCompleteFilter),
    )
    search_fields = ("user__username",)
    ordering = ("user__username",)
    autocomplete_fields = ("user", "application")

    def get_queryset(self, request: "HttpRequest") -> "QuerySet[ApplicationMembership]":
        return super().get_queryset(request).select_related("user", "application")
