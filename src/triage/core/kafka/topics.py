from triage.config import get_settings

_settings = get_settings()

class Topics:
    TESTABLE_READY_FOR_TESTING = _settings.kafka_topic_testable_ready_for_testing
    MEMBER_AVAILABILITY_CHANGED = _settings.kafka_topic_member_availability_changed
    ASSIGNMENT_COMPLETED = _settings.kafka_topic_assignment_completed

    TESTABLE_READY_FOR_TESTING_DLQ = _settings.kafka_topic_testable_ready_for_testing_dlq
    MEMBER_AVAILABILITY_CHANGED_DLQ = _settings.kafka_topic_member_availability_changed_dlq
    ASSIGNMENT_COMPLETED_DLQ = _settings.kafka_topic_assignment_completed_dlq

class ConsumerGroups:
    ASSIGNMENT = "assignment-engine"
    REBALANCING = "rebalancing-engine"
    NOTIFICATION = "notification-service"
