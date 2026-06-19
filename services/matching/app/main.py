import logging
import os
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching")

HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))


def start_nats(process_message):
    from app.nats_consumer import start_nats_consumer

    thread = threading.Thread(target=start_nats_consumer, args=(process_message,), daemon=True)
    thread.start()
    logger.info("NATS consumer started")


if __name__ == "__main__":
    from app.bootstrap import bootstrap_models

    bootstrap_models()

    from app.grpc_server import app, process_message, start as start_grpc
    from app.models_watcher import start_models_watcher

    start_grpc()
    start_models_watcher()
    start_nats(process_message)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)
