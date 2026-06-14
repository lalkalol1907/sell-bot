from unittest.mock import MagicMock, patch

import pytest

from app.grpc_server import process_message


@pytest.fixture
def core_client():
    client = MagicMock()
    client.get_seller.return_value = {
        "tg_user_id": 12345,
        "sensitivity": "precise",
        "spam_phrases": [],
    }
    client.list_products.return_value = [
        {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]},
    ]
    client.create_lead.return_value = 42
    return client


class TestProcessMessage:
    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_creates_lead_on_match(self, mock_get_core, mock_dedup, core_client):
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
        payload = core_client.create_lead.call_args[0][0]
        assert payload["product_title"] == "iPhone 16"
        assert payload["chat_title"] == "Тестовый чат"

    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_skips_duplicate(self, mock_get_core, mock_dedup, core_client):
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

    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_releases_dedup_on_create_failure(self, mock_get_core, mock_dedup, core_client):
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

    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_no_match_skips_lead(self, mock_get_core, mock_dedup, core_client):
        mock_get_core.return_value = core_client

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

    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_filters_short_spam(self, mock_get_core, mock_dedup, core_client):
        mock_get_core.return_value = core_client

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Чат",
            raw_text="куплю",
        )

        assert result["matched"] is False
        assert result["reason"] == "spam_length"
        core_client.create_lead.assert_not_called()

    @patch("app.grpc_server.dedup")
    @patch("app.grpc_server.get_core_client")
    def test_filters_learned_spam(self, mock_get_core, mock_dedup, core_client):
        core_client.get_seller.return_value["spam_phrases"] = ["курс по заработку"]
        mock_get_core.return_value = core_client

        result = process_message(
            seller_id=1,
            worker_id=2,
            chat_id=-100123,
            message_id=99,
            author_id=555,
            author_username="buyer",
            chat_title="Чат",
            raw_text="ищу курс по заработку в телеграм",
        )

        assert result["matched"] is False
        assert result["reason"] == "spam_learned"
        core_client.create_lead.assert_not_called()
