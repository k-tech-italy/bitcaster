from typing import TYPE_CHECKING, TypedDict
from unittest import mock
from unittest.mock import MagicMock

import pytest
from django.test.client import RequestFactory
from rest_framework.test import APIClient
from testutils.factories import ApiKeyFactory, EventFactory, ProjectFactory, UserFactory
from testutils.perms import key_grants

from bitcaster.api.event import EventTrigger
from bitcaster.api.permissions import ApiApplicationPermission, ApiBasePermission
from bitcaster.auth.constants import Grant
from bitcaster.exceptions import InvalidGrantError

if TYPE_CHECKING:
    from _pytest._code import ExceptionInfo

    from bitcaster.models import ApiKey, Event, User

    Context = TypedDict(
        "Context",
        {
            "event": Event,
            "key": ApiKey,
            "key2": ApiKey,
            "backend": ApiApplicationPermission,
            "user": User,
            "view": EventTrigger,
        },
    )

pytestmark = [pytest.mark.api, pytest.mark.django_db]


@pytest.fixture()
def client() -> APIClient:
    c = APIClient()
    return c


@pytest.fixture()
def context(admin_user: "User") -> "Context":
    event: "Event" = EventFactory()
    # app2: "Application" = ApplicationFactory()
    key: ApiKey = ApiKeyFactory(user=admin_user, grants=[], application=event.application)
    key2: ApiKey = ApiKeyFactory(user=admin_user, grants=[], application__project=ProjectFactory())
    assert key.organization.slug != key2.organization.slug
    return {
        "user": UserFactory(is_staff=True),
        "event": event,
        "key": key,
        "key2": key2,
        "backend": ApiApplicationPermission(),
        "view": MagicMock(specs=EventTrigger.as_view()),
    }


@pytest.mark.parametrize("g", [g for g in Grant])
def test_has_specific_permission(rf: RequestFactory, g: Grant, context: "Context") -> None:
    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    req = rf.get("/")

    with mock.patch.object(req, "auth", api_key, create=True):
        with mock.patch.object(view, "grants", [g], create=True):
            with key_grants(api_key, [g]):
                assert p.has_permission(req, view)


def test_scope(rf: RequestFactory, context: "Context") -> None:
    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    event: "Event" = context["event"]

    req = rf.get("/")

    view.required_grants = [Grant.SYSTEM_PING]
    view.kwargs = {
        "org": event.application.organization.slug,
        "prj": event.application.project.slug,
        "app": event.application.slug,
    }
    assert api_key.application.slug == event.application.slug
    with mock.patch.object(req, "auth", api_key, create=True):
        with key_grants(api_key, [Grant.SYSTEM_PING]):
            with mock.patch.object(view, "grants", [Grant.SYSTEM_PING]):
                assert p.has_permission(req, view)
                assert p.has_object_permission(req, view, event)


def test_invalid_scope(rf: RequestFactory, context: "Context") -> None:
    api_key: ApiKey = context["key2"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    event: "Event" = context["event"]

    req = rf.get("/")

    view.required_grants = [Grant.SYSTEM_PING]
    view.kwargs = {
        "org": event.application.organization.slug,
        "prj": event.application.project.slug,
        "app": event.application.slug,
    }
    with mock.patch.object(req, "auth", api_key, create=True):
        with key_grants(api_key, [Grant.SYSTEM_PING], application=None):
            with mock.patch.object(view, "grants", [Grant.SYSTEM_PING]):
                with pytest.raises(InvalidGrantError):
                    p.has_permission(req, view)
                with pytest.raises(InvalidGrantError):
                    p.has_object_permission(req, view, event)


def test_has_permission(rf: RequestFactory, context: "Context") -> None:
    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    req = rf.get("/")

    assert not p.has_permission(req, MagicMock())

    with mock.patch.object(req, "auth", None, create=True):
        assert not p.has_permission(req, MagicMock())

    with mock.patch.object(req, "auth", api_key, create=True):
        with mock.patch.object(view, "grants", [Grant.SYSTEM_PING], create=True):
            with mock.patch.object(view, "required_grants", [Grant.SYSTEM_PING], create=True):
                with key_grants(api_key, None):
                    assert not p.has_permission(req, view)

                with key_grants(api_key, None):
                    assert not p.has_permission(req, view)

        with mock.patch.object(view, "grants", [Grant.SYSTEM_PING], create=True):
            with mock.patch.object(view, "required_grants", [Grant.SYSTEM_PING], create=True):
                with key_grants(api_key, [Grant.SYSTEM_PING]):
                    assert p.has_permission(req, view)


def test_user_inactive(rf: RequestFactory, context: "Context") -> None:
    from django.contrib.auth.models import AnonymousUser

    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    req = rf.get("/")

    with mock.patch.object(req, "user", AnonymousUser(), create=True):
        with mock.patch.object(req, "auth", api_key, create=True):
            with mock.patch.object(view, "grants", [Grant.SYSTEM_PING]):
                with mock.patch.object(view, "required_grants", [Grant.SYSTEM_PING]):
                    with key_grants(api_key, None):
                        assert not p.has_permission(req, view)

    with mock.patch.object(req, "auth", None, create=True):
        with mock.patch.object(req, "user", context["key"].user, create=True):
            assert p.has_permission(req, view)

        with mock.patch.object(req, "user", context["user"], create=True):
            assert not p.has_permission(req, view)


def test_has_object_permission(rf: RequestFactory, context: "Context") -> None:
    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    event: "Event" = context["event"]
    req = rf.get("/")
    assert not p.has_permission(req, MagicMock())

    with mock.patch.object(req, "auth", None, create=True):
        assert not p.has_object_permission(req, MagicMock(), event)

    with mock.patch.object(req, "auth", api_key, create=True):
        with mock.patch.object(view, "grants", [Grant.SYSTEM_PING]):
            with mock.patch.object(view, "required_grants", [Grant.SYSTEM_PING]):
                with key_grants(api_key, None):
                    assert not p.has_object_permission(req, view, event)

        with key_grants(api_key, None):
            assert not p.has_object_permission(req, view, event)

        with mock.patch.object(view, "grants", [Grant.SYSTEM_PING]):
            with key_grants(api_key, Grant.SYSTEM_PING):
                assert p.has_object_permission(req, view, event)

    with mock.patch.object(req, "auth", None, create=True):
        with mock.patch.object(req, "user", context["key"].user, create=True):
            assert p.has_object_permission(req, view, event)

        with mock.patch.object(req, "user", context["user"], create=True):
            assert not p.has_object_permission(req, view, event)


def test_valid_scope(rf: RequestFactory, context: "Context") -> None:
    api_key: ApiKey = context["key"]
    p: ApiBasePermission = context["backend"]
    view: "EventTrigger" = context["view"]
    event: "Event" = context["event"]
    req = rf.get("/")
    exc: ExceptionInfo[Exception]
    assert not p.has_permission(req, MagicMock())

    with mock.patch.object(req, "auth", api_key, create=True):
        # Organization
        with mock.patch.object(view, "kwargs", {"org": event.application.project.organization.slug}):
            p.has_object_permission(req, view, event)

        with mock.patch.object(view, "kwargs", {"org": "---"}):
            with pytest.raises(InvalidGrantError) as exc:
                p.has_object_permission(req, view, event)
            assert str(exc.value) == f"Invalid organization for {api_key}"

        # Project
        with mock.patch.object(
            view, "kwargs", {"org": event.application.project.organization.slug, "prj": event.application.project.slug}
        ):
            p.has_object_permission(req, view, event)

        with mock.patch.object(view, "kwargs", {"org": event.application.project.organization.slug, "prj": "---"}):
            with pytest.raises(InvalidGrantError) as exc:
                p.has_object_permission(req, view, event)
            assert str(exc.value) == f"Invalid project for {api_key}"

        with mock.patch.object(
            view, "kwargs", {"org": event.application.project.organization.slug, "prj": event.application.project.slug}
        ):
            with key_grants(api_key, project=None):
                with pytest.raises(InvalidGrantError) as exc:
                    p.has_object_permission(req, view, event)
                assert str(exc.value) == "Key not enabled form project scope"

        # Application
        with mock.patch.object(
            view,
            "kwargs",
            {
                "org": event.application.project.organization.slug,
                "prj": event.application.project.slug,
                "app": event.application.slug,
            },
        ):
            p.has_object_permission(req, view, event)

        with mock.patch.object(
            view,
            "kwargs",
            {"org": event.application.project.organization.slug, "prj": event.application.project.slug, "app": "---"},
        ):
            with pytest.raises(InvalidGrantError) as exc:
                p.has_object_permission(req, view, event)
            assert str(exc.value) == f"Invalid application for {api_key}"

        with mock.patch.object(
            view,
            "kwargs",
            {
                "org": event.application.project.organization.slug,
                "prj": event.application.project.slug,
                "app": event.application.slug,
            },
        ):
            with key_grants(api_key, project=event.application.project, application=None):
                with pytest.raises(InvalidGrantError) as exc:
                    p.has_object_permission(req, view, event)
                assert str(exc.value) == "Key not enabled form application scope"
