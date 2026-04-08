from typing import Dict, List
from app.models import TaskSpec, Ticket


AVAILABLE_QUEUES: List[str] = [
    "general",
    "billing",
    "tech",
    "account",
    "security",
    "human_escalation",
]

AVAILABLE_TAGS: List[str] = [
    "refund",
    "bug",
    "login_issue",
    "suspicious_activity",
    "priority_customer",
    "needs_docs",
    "sensitive",
    "follow_up",
    "outage",
    "verification_required",
    "duplicate_charge",
    "security_incident",
]


TASK_LIBRARY: Dict[str, Dict] = {
    "easy_refund_request": {
        "task": TaskSpec(
            task_id="easy_refund_request",
            difficulty="easy",
            objective="Correctly triage a duplicate-charge refund request to the right team with appropriate priority and tags.",
            expected_steps=2,
            allowed_actions=["queue", "response_type", "priority", "tags", "redact_pii", "note"],
        ),
        "ticket": Ticket(
            ticket_id="TCK-E-1001",
            customer_tier="pro",
            category="refund",
            priority="medium",
            sentiment="calm",
            requires_human=False,
            contains_pii=False,
            summary="Customer reports a duplicate charge on last month's invoice and requests a refund.",
        ),
        "target": {
            "queue": "billing",
            "response_type": "reply",
            "priority": "medium",
            "must_tags": {"refund", "duplicate_charge"},
            "optional_tags": {"priority_customer"},
            "redact_pii": False,
            "must_escalate_human": False,
            "close_allowed": False,
        },
    },
    "medium_login_locked": {
        "task": TaskSpec(
            task_id="medium_login_locked",
            difficulty="medium",
            objective="Handle an account access issue requiring safe routing and follow-up for identity verification.",
            expected_steps=2,
            allowed_actions=["queue", "response_type", "priority", "tags", "redact_pii", "note"],
        ),
        "ticket": Ticket(
            ticket_id="TCK-M-2001",
            customer_tier="free",
            category="account",
            priority="high",
            sentiment="frustrated",
            requires_human=False,
            contains_pii=False,
            summary="Customer cannot access account after password reset. 2FA codes are not working and login attempts fail.",
        ),
        "target": {
            "queue": "account",
            "response_type": "request_info",
            "priority": "high",
            "must_tags": {"login_issue", "verification_required", "follow_up"},
            "optional_tags": {"needs_docs"},
            "redact_pii": False,
            "must_escalate_human": False,
            "close_allowed": False,
        },
    },
    "hard_security_breach": {
        "task": TaskSpec(
            task_id="hard_security_breach",
            difficulty="hard",
            objective="Safely triage an enterprise account takeover report with sensitive information, urgent escalation, and security routing.",
            expected_steps=3,
            allowed_actions=["queue", "response_type", "priority", "tags", "redact_pii", "note"],
        ),
        "ticket": Ticket(
            ticket_id="TCK-H-3001",
            customer_tier="enterprise",
            category="security",
            priority="urgent",
            sentiment="angry",
            requires_human=True,
            contains_pii=True,
            summary="Enterprise admin reports suspicious account takeover and included employee phone numbers plus internal IDs in the complaint.",
        ),
        "target": {
            "queue": "security",
            "response_type": "escalate",
            "priority": "urgent",
            "must_tags": {"suspicious_activity", "sensitive", "priority_customer", "security_incident"},
            "optional_tags": {"follow_up"},
            "redact_pii": True,
            "must_escalate_human": True,
            "close_allowed": False,
        },
    },
}


def list_task_ids() -> List[str]:
    return list(TASK_LIBRARY.keys())


def get_task_bundle(task_id: str) -> Dict:
    if task_id not in TASK_LIBRARY:
        raise ValueError(f"Unknown task_id: {task_id}")
    return TASK_LIBRARY[task_id]