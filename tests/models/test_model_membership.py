import pytest
from testutils.factories import ApplicationMembershipFactory

pytestmark = [pytest.mark.django_db]


@pytest.mark.parametrize(
    "locked, active, enable_notifications, expected",
    [
        pytest.param(False, True, True, True, id="receiving"),
        pytest.param(True, True, True, False, id="locked"),
        pytest.param(False, False, True, False, id="inactive"),
        pytest.param(False, True, False, False, id="notifications-disabled"),
    ],
)
def test_can_receive_notifications(locked: bool, active: bool, enable_notifications: bool, expected: bool) -> None:
    membership = ApplicationMembershipFactory(locked=locked, active=active, enable_notifications=enable_notifications)
    assert membership.can_receive_notifications is expected
