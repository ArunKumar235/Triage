import asyncio
from aiokafka import AIOKafkaConsumer, OffsetAndMetadata

from triage.config import get_settings
from triage.core.kafka.topics import ConsumerGroups, Topics
from triage.models.schemas.kafka_events import TestableReadyForTestingEvent, AssignmentCompletedEvent
from triage.core.kafka.producer import get_producer
from triage.core.graph.assignment_graph import run_assignment_graph
from triage.api.deps import get_session_factory
from triage.repositories.assignment_repo import AssignmentRepository
from triage.repositories.testable_repo import TestableRepository

async def consume_assignment_events(stop_event: asyncio.Event | None = None) -> None:
    settings = get_settings()
    producer = get_producer(settings)

    consumer = AIOKafkaConsumer(
        Topics.TESTABLE_READY_FOR_TESTING,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=ConsumerGroups.ASSIGNMENT,
        value_deserializer=lambda v: v.decode("utf-8"),
        enable_auto_commit=False # We will manually commit offsets after processing messages
    )

    await consumer.start()

    try:
        while not (stop_event and stop_event.is_set()):
            try:
                # `getmany` lets us poll the stop event between batches so
                # shutdown doesn't have to wait for the next broker message.
                batches = await consumer.getmany(timeout_ms=1000)
            except Exception:
                # Broker hiccup — back off and let the loop retry.
                await asyncio.sleep(1)
                continue

            for tp, messages in batches.items():
                for message in messages:
                    try:
                        event = TestableReadyForTestingEvent.model_validate_json(message.value)

                        # Runs eligibility -> capacity -> expertise (RAG) ->
                        # constraint scorer -> orchestrator LLM and returns a
                        # structured AssignmentDecision.
                        decision = await run_assignment_graph(event)

                        session_factory = get_session_factory()
                        async with session_factory() as session:
                            assignment_repo = AssignmentRepository(session)
                            testable_repo = TestableRepository(session)

                            await assignment_repo.save_decision(event.testable_id, event.team_id, decision)
                            await testable_repo.assign_tester_to_testable(event.testable_id, decision.top_candidate_id)

                        completed = AssignmentCompletedEvent(
                            testable_id=event.testable_id,
                            team_id=event.team_id,
                            assigned_to=decision.top_candidate_id,
                            confidence=decision.confidence,
                            reasoning=decision.reasoning
                        )

                        await producer.publish(
                            topic=Topics.ASSIGNMENT_COMPLETED,
                            value=completed.model_dump_json(),
                            key=event.testable_id
                        )

                        # Commit EXACTLY this message's offset + 1
                        # We add +1 because Kafka expects the offset of the *next* message to be read
                        offset_metadata = OffsetAndMetadata(message.offset + 1, "")
                        await consumer.commit({tp: offset_metadata})

                    except Exception as e:
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
                                topic=Topics.TESTABLE_READY_FOR_TESTING,
                                value=message.value,
                                key=message.key.decode("utf-8") if message.key else None,
                                headers=new_headers
                            )
                        else:
                            new_headers.append(("retry_count", str(retry_count).encode("utf-8")))
                            
                            await producer.publish(
                                topic=Topics.TESTABLE_READY_FOR_TESTING_DLQ,
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
    asyncio.run(consume_assignment_events())
