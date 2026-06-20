"""Application entrypoint: bootstrap models, start transport layers."""

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching")

HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))


if __name__ == "__main__":
    from app.bootstrap import bootstrap_models

    bootstrap_models()

    from app.handlers.message_processor import process_message
    from app.models_watcher import start_models_watcher
    from app.transport.grpc_server import start as start_grpc
    from app.transport.http_app import app
    from app.transport.nats_consumer import start_nats_consumer
    import threading

    start_grpc()
    start_models_watcher()

    nats_thread = threading.Thread(
        target=start_nats_consumer,
        args=(process_message,),
        daemon=True,
    )
    nats_thread.start()
    logger.info("NATS consumer started")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)
