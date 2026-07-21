import asyncio
from aiokafka import AIOKafkaConsumer, OffsetAndMetadata

from triage.config import get_settings
from triage.core.kafka.topics import ConsumerGroups, Topics
from triage.core.notifications.email_sender import send_assignment_email
from triage.models.schemas.kafka_events import AssignmentCompletedEvent
from triage.core.kafka.producer import get_producer

async def consume_notification_events(stop_event: asyncio.Event | None = None):
    settings = get_settings()

    consumer = AIOKafkaConsumer(
        Topics.ASSIGNMENT_COMPLETED,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=ConsumerGroups.NOTIFICATION,
        value_deserializer=lambda v: v.decode("utf-8"),
        enable_auto_commit=False
    )

    await consumer.start()

    try:
        while not (stop_event and stop_event.is_set()):
            try:
                batches = await consumer.getmany(timeout_ms=1000)
            except Exception:
                await asyncio.sleep(1)
                continue

            for tp, messages in batches.items():
                for message in messages:
                    try:
                        event = AssignmentCompletedEvent.model_validate_json(message.value)

                        # Send notification email to the team member about the assignment result
                        await send_assignment_email(event)

                        # Commit EXACTLY this message's offset + 1
                        # We add +1 because Kafka expects the offset of the *next* message to be read
                        offset_metadata = OffsetAndMetadata(message.offset + 1, "")
                        await consumer.commit({tp: offset_metadata})

                    except Exception as e:
                        producer = get_producer(settings)
                        max_retries = 3
                        retry_count = 0

                        if message.headers is not None:
                            for key, value in message.headers:
                                if key == "retry_count":
                                    retry_count = int(value.decode("utf-8"))
                        
                        new_headers = [
                            ("error_reason", str(e).encode("utf-8")),
                        ]

                        if(retry_count < max_retries):
                            new_retry_count = retry_count + 1
                            new_headers.append(("retry_count", str(new_retry_count).encode("utf-8")))
                            await producer.publish(
                                topic=Topics.ASSIGNMENT_COMPLETED,
                                value=message.value,
                                key=message.key.decode("utf-8") if message.key else None,
                                headers=new_headers
                            )
                        else:
                            new_headers.append(("retry_count", str(retry_count).encode("utf-8")))
                            
                            await producer.publish(
                                topic=Topics.ASSIGNMENT_COMPLETED_DLQ,
                                value=message.value,
                                key=message.key.decode("utf-8") if message.key else None,
                                headers=new_headers
                            )

                        # Commit it so it doesn't block the partition
                        offset_metadata = OffsetAndMetadata(message.offset + 1, "")
                        await consumer.commit({tp: offset_metadata})

    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_notification_events())
