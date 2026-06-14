from unittest.mock import MagicMock

import pytest

from app.dedup import DedupStore


@pytest.fixture
def dedup():
    store = DedupStore.__new__(DedupStore)
    store._client = MagicMock()
    store._ttl = 3600
    return store


class TestDedupStore:
    def test_key_format(self):
        key = DedupStore._key(100, 200, 3)
        assert key.startswith("dedup:")
        assert len(key) == len("dedup:") + 16

    def test_key_is_stable(self):
        assert DedupStore._key(1, 2, 3) == DedupStore._key(1, 2, 3)

    def test_try_reserve_first_call_succeeds(self, dedup):
        dedup._client.set.return_value = True
        assert dedup.try_reserve(1, 2, 3) is True
        dedup._client.set.assert_called_once_with(DedupStore._key(1, 2, 3), "1", nx=True, ex=3600)

    def test_try_reserve_second_call_fails(self, dedup):
        dedup._client.set.return_value = False
        assert dedup.try_reserve(1, 2, 3) is False

    def test_release_deletes_key(self, dedup):
        dedup.release(1, 2, 3)
        dedup._client.delete.assert_called_once()

    def test_is_duplicate_wraps_try_reserve(self, dedup):
        dedup._client.set.return_value = True
        assert dedup.is_duplicate(1, 2, 3) is False
        dedup._client.set.return_value = False
        assert dedup.is_duplicate(1, 2, 3) is True

    def test_different_authors_independent(self, dedup):
        dedup._client.set.return_value = True
        assert dedup.try_reserve(1, 2, 3) is True
        assert dedup.try_reserve(1, 99, 3) is True
        assert dedup._client.set.call_count == 2
