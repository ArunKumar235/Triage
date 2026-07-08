from __future__ import annotations

import json
from typing import Optional
from aiokafka import AIOKafkaProducer

from triage.config import Settings

_producer: Optional[KafkaProducerWrapper] = None

class KafkaProducerWrapper:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: Optional[AIOKafkaProducer] = None

    async def _ensure_started(self) -> AIOKafkaProducer:
        """
        Lazily initializes and starts the Kafka producer only during the first publish.
        """
        if self._client is None:
            self._client = AIOKafkaProducer(
                bootstrap_servers=self._settings.kafka_bootstrap_servers,
                value_serializer=lambda v: (
                    v.encode("utf-8") if isinstance(v, str) else json.dumps(v).encode("utf-8")
                )
            )
            await self._client.start()
        return self._client

    async def publish(self, topic: str, value: str, key: str | None = None, headers: list[tuple[str, bytes]] | None = None):
        client = await self._ensure_started()
        await client.send_and_wait(
            topic, 
            value=value, 
            key=key.encode("utf-8") if key else None,
            headers=headers
        )
    async def close(self):
        if self._client is not None:
            await self._client.stop()
            self._client = None

def get_producer(settings: Settings) -> KafkaProducerWrapper:
    global _producer
    if _producer is None:
        _producer = KafkaProducerWrapper(settings)
    return _producer

async def close_producer():
    global _producer
    if _producer is not None:
        await _producer.close()
        _producer = None
