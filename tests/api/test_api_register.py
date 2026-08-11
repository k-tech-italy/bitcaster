from typing import TYPE_CHECKING, Any

from rest_framework.test import APIClient

import pytest
from testutils.factories import (
    ApiKeyFactory,
    ChannelFactory,
    DistributionListFactory,
    EventFactory,
    UserFactory,
)
from testutils.perms import key_grants

from strategy_field.utils import fqn

from bitcaster.auth.constants import Grant
from bitcaster.dispatchers.email import EmailDispatcher
from bitcaster.models import ApplicationMembership, Assignment, User

if TYPE_CHECKING:
    from bitcaster.models import ApiKey, Application, Channel, DistributionList, Event

pytestmark = [pytest.mark.api, pytest.mark.django_db]

org_slug = "org-reg"
prj_slug = "prj-reg"
app_slug = "app-reg"


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

    email_channel: Channel = ChannelFactory(
        project=app.project, dispatcher=fqn(EmailDispatcher), preferred=True, name="prj-email"
    )
    dl: DistributionList = DistributionListFactory(project=app.project, application=app, name="customers")
    dl_other_app: DistributionList = DistributionListFactory(project=app.project, application=other_app, name="others")

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
        "other_app": other_app,
        "email_channel": email_channel,
        "dl": dl,
        "dl_other_app": dl_other_app,
        "key": key,
    }


@pytest.fixture
def client(data: dict[str, Any]) -> APIClient:
    c = APIClient()
    c._key = data["key"]
    c.credentials(HTTP_AUTHORIZATION=f"Key {data['key'].key}")
    return c


def url(data: dict[str, Any], app: "Application | None" = None) -> str:
    app = app or data["app"]
    return f"/api/o/{data['org'].slug}/p/{data['prj'].slug}/a/{app.slug}/register/"


def payload(**kwargs: Any) -> dict[str, Any]:
    ret: dict[str, Any] = {
        "username": "member1",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "custom_fields": {"plan": "gold"},
        "addresses": [
            {"value": "jane@example.com", "assign_to_preferred_channel": True},
        ],
        "distribution_list": "customers",
    }
    ret.update(kwargs)
    return ret


def grants(data: dict[str, Any]) -> Any:
    return key_grants(
        data["key"],
        [Grant.MANAGE_APPLICATION_USERS],
        organization=data["org"],
        project=data["prj"],
        application=data["app"],
    )


def test_register_requires_grant(client: APIClient, data: dict[str, Any]) -> None:
    res = client.post(url(data), payload(), format="json")
    assert res.status_code == 403


def test_register_creates_everything(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data), payload(), format="json")

    assert res.status_code == 201, res.json()
    body = res.json()
    assert body["created"] is True

    user = User.objects.get(username="member1")
    assert user.first_name == "Jane"
    assert user.roles.filter(organization=data["org"]).exists()

    membership = ApplicationMembership.objects.get(user=user, application=data["app"])
    assert membership.custom_fields == {"plan": "gold"}
    assert user.custom_fields == {}

    address = user.addresses.get(value="jane@example.com")
    assert address.name == "email"
    assignment = Assignment.objects.get(address=address, channel=data["email_channel"])
    assert assignment.validated is True
    assert assignment.active is True

    assert data["dl"].recipients.filter(pk=assignment.pk).exists()
    assert body["distribution_list"] == {"name": "customers", "recipients_added": 1}


def test_register_existing_user_not_updated(client: APIClient, data: dict[str, Any]) -> None:
    UserFactory(username="member1", first_name="Original", last_name="Name")
    with grants(data):
        res = client.post(url(data), payload(), format="json")

    assert res.status_code == 200, res.json()
    assert res.json()["created"] is False
    user = User.objects.get(username="member1")
    assert user.first_name == "Original"


def test_register_is_idempotent(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res1 = client.post(url(data), payload(), format="json")
        res2 = client.post(url(data), payload(), format="json")

    assert res1.status_code == 201
    assert res2.status_code == 200
    user = User.objects.get(username="member1")
    assert user.addresses.count() == 1
    assert Assignment.objects.filter(address__user=user).count() == 1
    assert ApplicationMembership.objects.filter(user=user).count() == 1
    assert data["dl"].recipients.count() == 1
    assert res2.json()["distribution_list"] == {"name": "customers", "recipients_added": 0}


def test_register_sets_membership_active(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data), payload(active=False), format="json")

    assert res.status_code == 201, res.json()
    assert res.json()["membership"] == {
        "custom_fields": {"plan": "gold"},
        "active": False,
        "locked": False,
        "enable_notifications": True,
    }
    membership = ApplicationMembership.objects.get(user__username="member1", application=data["app"])
    assert membership.active is False

    # re-register without "active" resets it to the default (True); locked/enable_notifications untouched
    membership.locked = True
    membership.enable_notifications = False
    membership.save()
    with grants(data):
        client.post(url(data), payload(), format="json")
    membership.refresh_from_db()
    assert membership.active is True
    assert membership.locked is True
    assert membership.enable_notifications is False


def test_register_merges_custom_fields(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        client.post(url(data), payload(), format="json")
        client.post(url(data), payload(custom_fields={"tier": 2}), format="json")

    membership = ApplicationMembership.objects.get(user__username="member1", application=data["app"])
    assert membership.custom_fields == {"plan": "gold", "tier": 2}


def test_register_custom_fields_isolated_per_application(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res1 = client.post(url(data), payload(distribution_list=None), format="json")

    with key_grants(
        data["key"],
        [Grant.MANAGE_APPLICATION_USERS],
        organization=data["org"],
        project=data["prj"],
        application=data["other_app"],
    ):
        res2 = client.post(
            url(data, data["other_app"]),
            payload(custom_fields={"plan": "silver"}, distribution_list=None),
            format="json",
        )

    assert res1.status_code == 201
    assert res2.status_code == 200
    user = User.objects.get(username="member1")
    assert user.memberships.get(application=data["app"]).custom_fields == {"plan": "gold"}
    assert user.memberships.get(application=data["other_app"]).custom_fields == {"plan": "silver"}


def test_register_no_compatible_channel_is_skipped(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(
            url(data),
            payload(
                addresses=[{"value": "+39123456789", "assign_to_preferred_channel": True}],
                distribution_list=None,
            ),
            format="json",
        )

    assert res.status_code == 201, res.json()
    body = res.json()
    assert body["assignments"] == [{"address": "+39123456789", "channel": None, "skipped": True}]
    user = User.objects.get(username="member1")
    assert user.addresses.get(value="+39123456789").type == "phone"
    assert not Assignment.objects.filter(address__user=user).exists()


def test_register_does_not_reset_validated(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        client.post(url(data), payload(), format="json")

    assignment = Assignment.objects.get(address__user__username="member1")
    assignment.validated = False
    assignment.save()

    with grants(data):
        client.post(url(data), payload(), format="json")

    assignment.refresh_from_db()
    assert assignment.validated is False


def test_register_unknown_distribution_list(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data), payload(distribution_list="nope"), format="json")

    assert res.status_code == 400
    assert "does not exist" in res.json()["distribution_list"]
    assert not User.objects.filter(username="member1").exists()


def test_register_distribution_list_pinned_to_other_app(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data), payload(distribution_list="others"), format="json")

    assert res.status_code == 400
    assert "pinned to another application" in res.json()["distribution_list"]


def test_register_unknown_application(client: APIClient, data: dict[str, Any]) -> None:
    # with key auth the scope check rejects a mismatching app slug before the view runs
    with grants(data):
        res = client.post(
            f"/api/o/{data['org'].slug}/p/{data['prj'].slug}/a/missing-app/register/", payload(), format="json"
        )

    assert res.status_code == 403


def test_register_unknown_application_as_superuser(admin_user: "User", data: dict[str, Any]) -> None:
    c = APIClient()
    c.force_authenticate(user=admin_user)
    res = c.post(f"/api/o/{data['org'].slug}/p/{data['prj'].slug}/a/missing-app/register/", payload(), format="json")
    assert res.status_code == 404


def test_register_requires_username(client: APIClient, data: dict[str, Any]) -> None:
    with grants(data):
        res = client.post(url(data), payload(username=None), format="json")

    assert res.status_code == 400
