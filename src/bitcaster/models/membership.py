from django.db import models
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

    objects = ApplicationMembershipManager()

    class Meta:
        verbose_name = _("Application Membership")
        verbose_name_plural = _("Application Memberships")
        unique_together = (("user", "application"),)

    def __str__(self) -> str:
        return f"{self.user} - {self.application}"

    def natural_key(self) -> tuple[str | None, ...]:
        return self.user.username, *self.application.natural_key()
