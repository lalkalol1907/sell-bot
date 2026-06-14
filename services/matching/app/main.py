import logging
import os
import threading

from app.grpc_server import app, process_message, start as start_grpc
from app.nats_consumer import start_nats_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching")

HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))


def start_nats():
    thread = threading.Thread(target=start_nats_consumer, args=(process_message,), daemon=True)
    thread.start()
    logger.info("NATS consumer started")


if __name__ == "__main__":
    start_grpc()
    start_nats()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)
