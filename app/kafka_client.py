import json
import logging
from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)
_producer: Any | None = None


def get_producer():
    global _producer

    if not settings.enable_kafka:
        return None

    if _producer is None:
        try:
            from confluent_kafka import Producer
        except ImportError:
            logger.warning(
                "Kafka is enabled, but confluent-kafka is not installed; "
                "click events will not be published."
            )
            return None

        _producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "client.id": "url-shortener-producer",
            }
        )

    return _producer


def publish_click_event(event: dict):
    """Fire-and-forget publish. Log failures without blocking redirects."""
    producer = get_producer()
    if producer is None:
        return

    try:
        producer.produce(
            settings.kafka_topic,
            value=json.dumps(event).encode("utf-8"),
            key=event.get("short_code", "").encode("utf-8"),
        )
        producer.poll(0)
    except Exception as exc:
        logger.warning("Kafka publish failed: %s", exc)
