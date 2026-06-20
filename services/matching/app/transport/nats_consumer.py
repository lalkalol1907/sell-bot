import asyncio
import json
import logging
import os

logger = logging.getLogger("matching.nats")

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
STREAM_NAME = "SELLBOT"
CONSUMER_NAME = "matching-captured"
SUBJECT = "message.captured"


async def _ensure_consumer(js):
    from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, RetentionPolicy, StorageType, StreamConfig

    try:
        await js.stream_info(STREAM_NAME)
    except Exception:
        await js.add_stream(
            StreamConfig(
                name=STREAM_NAME,
                subjects=["lead.created", "worker.status", SUBJECT],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
            )
        )
        logger.info("created JetStream stream %s", STREAM_NAME)

    try:
        await js.consumer_info(STREAM_NAME, CONSUMER_NAME)
    except Exception:
        await js.add_consumer(
            STREAM_NAME,
            ConsumerConfig(
                durable_name=CONSUMER_NAME,
                filter_subject=SUBJECT,
                deliver_policy=DeliverPolicy.ALL,
                ack_policy=AckPolicy.EXPLICIT,
                max_deliver=5,
            ),
        )
        logger.info("created JetStream consumer %s", CONSUMER_NAME)


async def _run(process_fn) -> None:
    import nats

    nc = await nats.connect(NATS_URL)
    js = nc.jetstream()
    await _ensure_consumer(js)
    sub = await js.pull_subscribe(SUBJECT, durable=CONSUMER_NAME, stream=STREAM_NAME)
    logger.info("JetStream pull consumer subscribed to %s", SUBJECT)

    while True:
        try:
            msgs = await sub.fetch(batch=10, timeout=5)
        except TimeoutError:
            continue
        except Exception as exc:
            logger.warning("fetch error: %s", exc)
            await asyncio.sleep(1)
            continue

        for msg in msgs:
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
                await msg.ack()
            except Exception as exc:
                logger.exception("message.captured handler error: %s", exc)
                await msg.nak()


def start_nats_consumer(process_fn) -> None:
    asyncio.run(_run(process_fn))
