"""Unit tests for transport layer (gRPC, NATS, HTTP metrics)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.generated import matching_pb2, matching_pb2_grpc


class TestGrpcServer:
    @patch("app.transport.grpc_server.process_message")
    def test_process_message_servicer(self, mock_process):
        from app.transport import grpc_server

        mock_process.return_value = {
            "matched": True,
            "lead_id": 7,
            "product_id": 3,
            "product_title": "iPhone 16",
            "score": 0.91,
            "level": "confirmed",
        }

        captured: dict = {}
        original_add = matching_pb2_grpc.add_MatchingServiceServicer_to_server

        def capture_add(servicer, server):
            captured["servicer"] = servicer
            return original_add(servicer, server)

        with patch.object(matching_pb2_grpc, "add_MatchingServiceServicer_to_server", capture_add):
            grpc_server._build_grpc_server()

        request = matching_pb2.ProcessMessageRequest(
            seller_id=1,
            worker_id=2,
            chat_id=-100,
            message_id=10,
            author_id=555,
            author_username="buyer",
            chat_title="Chat",
            raw_text="куплю айфон 16",
        )
        response = captured["servicer"].ProcessMessage(request, None)

        assert response.matched is True
        assert response.lead_id == 7
        assert response.product_id == 3
        assert response.product_title == "iPhone 16"
        assert response.score == pytest.approx(0.91)
        assert response.level == "confirmed"
        mock_process.assert_called_once()

    @patch("app.transport.grpc_server._build_grpc_server")
    def test_serve_grpc_starts_and_waits(self, mock_build):
        from app.transport.grpc_server import serve_grpc

        server = MagicMock()
        mock_build.return_value = server

        serve_grpc()

        server.start.assert_called_once()
        server.wait_for_termination.assert_called_once()

    @patch("app.transport.grpc_server.serve_grpc")
    def test_start_spawns_daemon_thread(self, mock_serve):
        from app.transport.grpc_server import start

        start()
        mock_serve.assert_called_once()


class TestNatsConsumer:
    def test_ensure_consumer_creates_stream_and_consumer(self):
        from app.transport.nats_consumer import _ensure_consumer

        async def run():
            js = AsyncMock()
            js.stream_info.side_effect = RuntimeError("missing stream")
            js.consumer_info.side_effect = RuntimeError("missing consumer")
            await _ensure_consumer(js)
            js.add_stream.assert_awaited_once()
            js.add_consumer.assert_awaited_once()

        asyncio.run(run())

    def test_ensure_consumer_skips_existing(self):
        from app.transport.nats_consumer import _ensure_consumer

        async def run():
            js = AsyncMock()
            await _ensure_consumer(js)
            js.add_stream.assert_not_awaited()
            js.add_consumer.assert_not_awaited()

        asyncio.run(run())

    def test_run_processes_and_acks_message(self):
        from app.transport import nats_consumer

        async def run():
            payload = {
                "seller_id": 1,
                "worker_id": 2,
                "chat_id": -100,
                "message_id": 11,
                "author_id": 555,
                "author_username": "buyer",
                "chat_title": "Chat",
                "raw_text": "куплю айфон",
            }
            msg = AsyncMock()
            msg.data = json.dumps(payload).encode()

            sub = AsyncMock()
            calls = {"n": 0}

            async def fetch_side_effect(*_args, **_kwargs):
                calls["n"] += 1
                if calls["n"] == 1:
                    return [msg]
                raise asyncio.CancelledError

            sub.fetch = fetch_side_effect

            js = AsyncMock()
            js.pull_subscribe = AsyncMock(return_value=sub)

            nc = AsyncMock()
            nc.jetstream = MagicMock(return_value=js)

            process_fn = MagicMock()

            with patch("nats.connect", AsyncMock(return_value=nc)):
                with patch.object(nats_consumer, "_ensure_consumer", AsyncMock()):
                    with pytest.raises(asyncio.CancelledError):
                        await nats_consumer._run(process_fn)

            process_fn.assert_called_once_with(
                seller_id=1,
                worker_id=2,
                chat_id=-100,
                message_id=11,
                author_id=555,
                author_username="buyer",
                chat_title="Chat",
                raw_text="куплю айфон",
            )
            msg.ack.assert_awaited_once()

        asyncio.run(run())

    def test_run_naks_on_handler_error(self):
        from app.transport import nats_consumer

        async def run():
            msg = AsyncMock()
            msg.data = b"{not-json"

            sub = AsyncMock()
            calls = {"n": 0}

            async def fetch_side_effect(*_args, **_kwargs):
                calls["n"] += 1
                if calls["n"] == 1:
                    return [msg]
                raise asyncio.CancelledError

            sub.fetch = fetch_side_effect
            js = AsyncMock()
            js.pull_subscribe = AsyncMock(return_value=sub)
            nc = AsyncMock()
            nc.jetstream = MagicMock(return_value=js)

            with patch("nats.connect", AsyncMock(return_value=nc)):
                with patch.object(nats_consumer, "_ensure_consumer", AsyncMock()):
                    with pytest.raises(asyncio.CancelledError):
                        await nats_consumer._run(MagicMock())

            msg.nak.assert_awaited_once()

        asyncio.run(run())

    def test_run_continues_after_fetch_error(self):
        from app.transport import nats_consumer

        async def run():
            sub = AsyncMock()
            calls = {"n": 0}

            async def fetch_side_effect(*_args, **_kwargs):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("fetch failed")
                raise asyncio.CancelledError

            sub.fetch = fetch_side_effect
            js = AsyncMock()
            js.pull_subscribe = AsyncMock(return_value=sub)
            nc = AsyncMock()
            nc.jetstream = MagicMock(return_value=js)

            with patch("nats.connect", AsyncMock(return_value=nc)):
                with patch.object(nats_consumer, "_ensure_consumer", AsyncMock()):
                    with patch.object(nats_consumer.asyncio, "sleep", AsyncMock()) as mock_sleep:
                        with pytest.raises(asyncio.CancelledError):
                            await nats_consumer._run(MagicMock())
                        mock_sleep.assert_awaited()

        asyncio.run(run())

    def test_start_nats_consumer_runs_loop(self):
        from app.transport import nats_consumer

        with patch.object(nats_consumer.asyncio, "run") as mock_run:
            nats_consumer.start_nats_consumer(MagicMock())
            mock_run.assert_called_once()


class TestHttpApp:
    def test_metrics_endpoint(self):
        from fastapi.testclient import TestClient

        from app.transport.http_app import app

        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
