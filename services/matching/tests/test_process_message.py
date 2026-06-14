from unittest.mock import MagicMock, patch

import pytest

from app.grpc_server import process_message


@pytest.fixture
def core_client():
    client = MagicMock()
    client.get_seller.return_value = {"tg_user_id": 12345, "sensitivity": "precise"}
    client.list_products.return_value = [
        {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]},
    ]
    client.create_lead.return_value = 42
    return client


class TestProcessMessage:
    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_creates_lead_on_match(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = True

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Тестовый чат",
            raw_text="куплю айфон 16",
        )

        assert result["matched"] is True
        assert result["lead_id"] == 42
        core_client.create_lead.assert_called_once()
        mock_publish.assert_called_once()
        event = mock_publish.call_args[0][0]
        assert event["lead_id"] == 42
        assert event["tg_user_id"] == 12345

    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_skips_duplicate(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = False

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Чат",
            raw_text="куплю айфон 16",
        )

        assert result["matched"] is False
        assert result["reason"] == "duplicate"
        core_client.create_lead.assert_not_called()
        mock_publish.assert_not_called()

    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_releases_dedup_on_create_failure(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = True
        core_client.create_lead.side_effect = RuntimeError("core down")

        with pytest.raises(RuntimeError):
            process_message(
                seller_id=1,
                worker_id=2,
                chat_id=-100123,
                message_id=99,
                author_id=555,
                author_username="buyer",
                chat_title="Чат",
                raw_text="куплю айфон 16",
            )

        mock_dedup.release.assert_called_once()
        mock_publish.assert_not_called()

    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_notify_failed_when_nats_down(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = True
        mock_publish.side_effect = RuntimeError("nats down")

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Чат",
            raw_text="куплю айфон 16",
        )

        assert result["matched"] is True
        assert result["lead_id"] == 42
        assert result["notify_failed"] is True

    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_no_match_skips_lead(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = True

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Чат",
            raw_text="погода сегодня отличная",
        )

        assert result["matched"] is False
        core_client.create_lead.assert_not_called()
        mock_publish.assert_not_called()

    @patch("app.grpc_server._publish_lead_created")
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_rejects_seller_message(self, mock_get_core, mock_dedup, mock_publish, core_client):
        mock_get_core.return_value = core_client
        mock_dedup.try_reserve.return_value = True

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="seller",
            chat_title="Чат",
            raw_text="продаю айфон 16",
        )

        assert result["matched"] is False
        core_client.create_lead.assert_not_called()
