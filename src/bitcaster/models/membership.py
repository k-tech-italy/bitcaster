from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from .application import Application
from .mixins import BitcasterBaseModel, BitcasterBaselManager
from .user import User


class ApplicationMembershipManager(BitcasterBaselManager["ApplicationMembership"]):
    def get_by_natural_key(self, user: str, app: str, prj: str, org: str) -> "ApplicationMembership":
        return self.get(
            user__username=user,
            application__slug=app,
            application__project__slug=prj,
            application__project__organization__slug=org,
        )

    def blocked_user_ids(self, application: "Application") -> "QuerySet[ApplicationMembership, int]":
        """Ids of users whose membership for the application prevents receiving notifications."""
        return (
            self.filter(application=application)
            .filter(Q(locked=True) | Q(active=False) | Q(enable_notifications=False))
            .values_list("user_id", flat=True)
        )


class ApplicationMembership(BitcasterBaseModel):
    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="memberships",
        help_text=_("member user"),
    )
    application = models.ForeignKey(
        Application,
        verbose_name=_("Application"),
        on_delete=models.CASCADE,
        related_name="memberships",
        help_text=_("application the user is member of"),
    )
    custom_fields = models.JSONField(
        verbose_name=_("Custom fields"),
        blank=True,
        default=dict,
        help_text=_("Member custom fields for this application"),
    )
    locked = models.BooleanField(
        verbose_name=_("locked"),
        default=False,
        help_text=_("Managed only via the admin. If checked no notification is sent to the user for this application"),
    )
    active = models.BooleanField(
        verbose_name=_("active"),
        default=True,
        help_text=_(
            "Mirrors the client application 'active' state for the user. "
            "If unchecked the user receives no notifications for this application"
        ),
    )
    enable_notifications = models.BooleanField(
        verbose_name=_("enable notifications"),
        default=True,
        help_text=_(
            "Whether the user receives notifications for this application (effective only when active and not locked)"
        ),
    )

    objects = ApplicationMembershipManager()

    class Meta:
        verbose_name = _("Application Membership")
        verbose_name_plural = _("Application Memberships")
        unique_together = (("user", "application"),)

    def __str__(self) -> str:
        return f"{self.user} - {self.application}"

    @property
    def can_receive_notifications(self) -> bool:
        return self.active and not self.locked and self.enable_notifications

    def natural_key(self) -> tuple[str | None, ...]:
        return self.user.username, *self.application.natural_key()
