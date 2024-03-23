from factory import Sequence
from factory.django import DjangoModelFactory

from bitcaster.config import Group
from bitcaster.models import User, Role, Sender


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = Sequence(lambda n: "user%03d" % n)
    email = Sequence(lambda n: "user%03d@localhost" % n)
    password = "test"


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ("name",)

    name = Sequence(lambda n: "role%03d" % n)


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = Sequence(lambda n: "group%03d" % n)


class SenderFactory(DjangoModelFactory):
    class Meta:
        model = Sender
        django_get_or_create = ("name",)

    name = Sequence(lambda n: "sender%03d" % n)
