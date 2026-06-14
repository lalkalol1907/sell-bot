import asyncio
import json
import logging
import os

logger = logging.getLogger("matching.nats")


async def _run(process_fn) -> None:
    import nats

    url = os.getenv("NATS_URL", "nats://nats:4222")

    async def handler(msg):
        try:
            payload = json.loads(msg.data.decode())
            process_fn(
                seller_id=int(payload["seller_id"]),
                worker_id=int(payload.get("worker_id", 0)),
                chat_id=int(payload["chat_id"]),
                message_id=int(payload["message_id"]),
                author_id=int(payload["author_id"]),
                author_username=payload.get("author_username", ""),
                chat_title=payload.get("chat_title", ""),
                raw_text=payload["raw_text"],
            )
        except Exception as exc:
            logger.exception("message.captured handler error: %s", exc)

    nc = await nats.connect(url)
    await nc.subscribe("message.captured", cb=handler)
    logger.info("subscribed to message.captured")
    await asyncio.Event().wait()


def start_nats_consumer(process_fn) -> None:
    asyncio.run(_run(process_fn))
