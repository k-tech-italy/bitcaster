import factory

from bitcaster.models import ApplicationMembership

from .base import AutoRegisterModelFactory
from .org import ApplicationFactory
from .user import UserFactory


class ApplicationMembershipFactory(AutoRegisterModelFactory[ApplicationMembership]):
    class Meta:
        model = ApplicationMembership
        django_get_or_create = ("user", "application")

    user = factory.SubFactory(UserFactory)
    application = factory.SubFactory(ApplicationFactory)
