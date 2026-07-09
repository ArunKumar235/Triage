from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from triage.config import Settings
from triage.core.kafka.topics import Topics

async def ensure_kafka_topics(settings: Settings):
    """
    Connects to the Kafka broker via the Admin client and ensures all 
    required topics exist. If they already exist, it fails gracefully.
    """
    admin_client = AIOKafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers
    )
    
    await admin_client.start()
    
    topic_names = [
        Topics.TESTABLE_READY_FOR_TESTING,
        Topics.MEMBER_AVAILABILITY_CHANGED,
        Topics.ASSIGNMENT_COMPLETED,
        Topics.TESTABLE_READY_FOR_TESTING_DLQ,
        Topics.MEMBER_AVAILABILITY_CHANGED_DLQ,
        Topics.ASSIGNMENT_COMPLETED_DLQ,
    ]
    
    # Define topics with 1 partition and 1 replication factor
    new_topics = [
        NewTopic(name=name, num_partitions=1, replication_factor=1)
        for name in topic_names
    ]

    try:
        await admin_client.create_topics(new_topics=new_topics)
        # print("Kafka topics verified/created successfully!")

    except Exception as e:
        # Ignore errors here, this typically means the topics already exist, 
        # or Kafka is just down (which will be caught by the consumers anyway)
        pass
    finally:
        await admin_client.close()
