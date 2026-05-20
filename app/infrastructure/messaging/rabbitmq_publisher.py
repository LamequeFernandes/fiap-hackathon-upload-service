import json
import logging
from uuid import UUID

import aio_pika

from app.application.ports.messaging_port import IMessagingPort
from app.core.config import settings
from app.domain.exceptions import MessagingError

logger = logging.getLogger(__name__)


class RabbitMQPublisher(IMessagingPort):
    async def publish_analysis(self, analysis_id: UUID, file_url: str) -> None:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(
                    settings.rabbitmq_exchange,
                    aio_pika.ExchangeType.DIRECT,
                    durable=True,
                )
                queue = await channel.declare_queue(
                    settings.rabbitmq_queue, durable=True
                )
                await queue.bind(
                    exchange, routing_key=settings.rabbitmq_routing_key
                )

                body = json.dumps(
                    {"analysis_id": str(analysis_id), "file_url": file_url}
                ).encode()

                await exchange.publish(
                    aio_pika.Message(
                        body=body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        content_type="application/json",
                    ),
                    routing_key=settings.rabbitmq_routing_key,
                )
                logger.info(
                    "Message published to RabbitMQ",
                    extra={
                        "event": "message_published",
                        "analysis_id": str(analysis_id),
                    },
                )
        except Exception as exc:
            raise MessagingError(f"Failed to publish message: {exc}") from exc
