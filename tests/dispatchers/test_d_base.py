import pytest
from strategy_field.utils import fqn

from bitcaster.dispatchers.base import dispatcherManager

pytestmark = [pytest.mark.dispatcher, pytest.mark.django_db]


def test_registry():
    from testutils.dispatcher import TestDispatcher

    assert TestDispatcher in dispatcherManager
    assert fqn(TestDispatcher) in dispatcherManager