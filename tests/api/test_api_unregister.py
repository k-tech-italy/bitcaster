from typing import TYPE_CHECKING, Any

from rest_framework.test import APIClient

import pytest
from testutils.factories import (
    ApiKeyFactory,
    ApplicationMembershipFactory,
    EventFactory,
    UserFactory,
)
from testutils.perms import key_grants

from bitcaster.auth.constants import Grant
from bitcaster.models import ApplicationMembership

if TYPE_CHECKING:
    from bitcaster.models import ApiKey, Application, Event, User

pytestmark = [pytest.mark.api, pytest.mark.django_db]

org_slug = "org-unregister"
prj_slug = "prj-unregister"
app_slug = "app-unregister"


@pytest.fixture
def data(admin_user: "User", system_objects: Any) -> dict[str, Any]:
    event: Event = EventFactory(
        application__project__organization__name=org_slug,
        application__project__name=prj_slug,
        application__name=app_slug,
        application__slug=app_slug,
    )
    app: Application = event.application
    other_event: Event = EventFactory(
        application__project__organization__name=org_slug,
        application__project__name=prj_slug,
    )
    other_app: Application = other_event.application

    user: "User" = UserFactory()
    membership = ApplicationMembershipFactory(user=user, application=app)
    other_membership = ApplicationMembershipFactory(user=user, application=other_app)

    key: "ApiKey" = ApiKeyFactory(
        user=admin_user,
        grants=[],
        application=None,
        project=None,
        organization=app.project.organization,
    )

    return {
        "org": app.project.organization,
        "prj": app.project,
        "app": app,
        "user": user,
        "key": key,
        "membership": membership,
        "other_membership": other_membership,
    }


@pytest.fixture
def client(data: dict[str, Any]) -> APIClient:
    c = APIClient()
    c._key = data["key"]
    c.credentials(HTTP_AUTHORIZATION=f"Key {data['key'].key}")
    return c


def url(data: dict[str, Any], username: str | None = None) -> str:
    username = username or data["user"].username
    return f"/api/o/{data['org'].slug}/p/{data['prj'].slug}/a/{data['app'].slug}/unregister/{username}/"


def grants(data: dict[str, Any]) -> Any:
    return key_grants(
        data["key"],
        [Grant.MANAGE_APPLICATION_USERS],
        organization=data["org"],
        project=data["prj"],
        application=data["app"],
    )


def test_unregister_requires_grant(client: APIClient, data: dict[str, Any]) -> None:
    res = client.post(url(data))
    assert res.status_code == 403


def test_unregister_deletes_membership_of_url_application_only(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data))

    assert res.status_code == 200
    assert res.json()["deleted"] == 1
    assert not ApplicationMembership.objects.filter(pk=data["membership"].pk).exists()
    assert ApplicationMembership.objects.filter(pk=data["other_membership"].pk).exists()


def test_unregister_is_idempotent(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res1 = client.post(url(data))
        res2 = client.post(url(data))

    assert res1.status_code == 200
    assert res1.json()["deleted"] == 1
    assert res2.status_code == 200
    assert res2.json()["deleted"] == 0


def test_unregister_unknown_user(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data, "missing-user"))

    assert res.status_code == 404


def test_unregister_uses_post_verb(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res_get = client.get(url(data))
        res_post = client.post(url(data))

    assert res_get.status_code == 405
    assert res_post.status_code == 200
