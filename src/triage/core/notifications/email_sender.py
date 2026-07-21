from email.message import EmailMessage
from pathlib import Path
import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from triage.config import get_settings
from triage.models.schemas.kafka_events import AssignmentCompletedEvent
from triage.repositories.team_member_repo import TeamMemberRepository
from triage.repositories.testable_repo import TestableRepository
from triage.api.deps import get_session_factory

TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

def _render_assignment_email(
    member_name: str,
    testable_id: str,
    app: str,
    feature: str,
    priority: str,
    confidence: float,
    reasoning: str,
) -> str:
    template = _jinja_env.get_template("assignment_email.html")
    return template.render(
        member_name=member_name,
        testable_id=testable_id,
        app=app,
        feature=feature,
        priority=priority,
        confidence=f"{confidence * 100:.0f}%",
        reasoning=reasoning,
    )


async def send_assignment_email(event: AssignmentCompletedEvent) -> None:
    """Looks up the assignee's contact details and the testable's display
    info, renders the HTML template, and sends it over SMTP.

    Contact info and testable details are looked up fresh here rather than
    carried on the Kafka event itself, since a display name or email can
    change between when the assignment ran and when this consumer picks up
    the message. Exceptions are allowed to propagate so the notification
    consumer leaves the offset uncommitted and retries, instead of silently
    dropping a notification on a transient SMTP failure.
    """
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        member_repo = TeamMemberRepository(session)
        testable_repo = TestableRepository(session)

        member = await member_repo.get_member_by_id(event.assigned_to)
        testable = await testable_repo.get_testable(event.testable_id)

        if not member or not testable:
            raise ValueError(f"Could not find member ({event.assigned_to}) or testable ({event.testable_id})")

    html_body = _render_assignment_email(
        member_name=member.display_name,
        testable_id=event.testable_id,
        app=testable.app,
        feature=testable.feature,
        priority=testable.priority,
        confidence=event.confidence,
        reasoning=event.reasoning,
    )

    message = EmailMessage()
    message["From"] = settings.notification_from_email
    message["To"] = member.email
    message["Subject"] = f"[{testable.priority.value if hasattr(testable.priority, 'value') else testable.priority}] You've been assigned {event.testable_id}"
    message.set_content("This email requires an HTML-capable client to view.")
    message.add_alternative(html_body, subtype="html")

    smtp_kwargs = {
        "hostname": settings.smtp_host,
        "port": settings.smtp_port,
        "start_tls": settings.smtp_starttls,
    }
    if settings.smtp_user:
        smtp_kwargs["username"] = settings.smtp_user
    if settings.smtp_password:
        smtp_kwargs["password"] = settings.smtp_password

    await aiosmtplib.send(
        message,
        **smtp_kwargs
    )
