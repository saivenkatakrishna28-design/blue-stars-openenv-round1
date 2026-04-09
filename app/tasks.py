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
    "policy_review",
    "sla_risk",
    "account_takeover",
    "billing_error",
    "identity_check",
]


TASK_LIBRARY: Dict[str, Dict] = {
    "easy_refund_request": {
        "task": TaskSpec(
            task_id="easy_refund_request",
            difficulty="easy",
            objective=(
                "Correctly triage a duplicate-charge refund request by routing it to billing, "
                "assigning an appropriate priority, and applying the correct refund-related tags."
            ),
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
            summary=(
                "Customer reports a duplicate charge on last month's invoice and requests a refund. "
                "Billing history shows the invoice was generated twice for the same subscription renewal. "
                "No fraud indicators are present. Customer wants confirmation of refund timeline."
            ),
        ),
        "target": {
            "queue": "billing",
            "response_type": "reply",
            "priority": "medium",
            "must_tags": {"refund", "duplicate_charge", "billing_error"},
            "optional_tags": {"priority_customer", "follow_up"},
            "redact_pii": False,
            "must_escalate_human": False,
            "close_allowed": False,
            "policy_rules": {
                "should_not_route_to_security": True,
                "should_acknowledge_resolution_path": True,
            },
            "task_context": {
                "business_impact": "low",
                "risk_level": "low",
                "sla_hours": 24,
            },
        },
    },
    "medium_login_locked": {
        "task": TaskSpec(
            task_id="medium_login_locked",
            difficulty="medium",
            objective=(
                "Handle an account access issue that requires secure follow-up, correct routing, "
                "identity verification awareness, and appropriate urgency."
            ),
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
            summary=(
                "Customer cannot access account after password reset. 2FA codes are not working and "
                "multiple login attempts have failed since a device change. No confirmed breach yet, "
                "but account recovery must be handled carefully. Customer asks for urgent help."
            ),
        ),
        "target": {
            "queue": "account",
            "response_type": "request_info",
            "priority": "high",
            "must_tags": {"login_issue", "verification_required", "follow_up", "identity_check"},
            "optional_tags": {"needs_docs", "policy_review"},
            "redact_pii": False,
            "must_escalate_human": False,
            "close_allowed": False,
            "policy_rules": {
                "must_verify_identity_before_resolution": True,
                "should_not_close_early": True,
            },
            "task_context": {
                "business_impact": "medium",
                "risk_level": "medium",
                "sla_hours": 8,
            },
        },
    },
    "hard_security_breach": {
        "task": TaskSpec(
            task_id="hard_security_breach",
            difficulty="hard",
            objective=(
                "Safely triage an enterprise account takeover report containing sensitive information, "
                "route it to security, escalate properly, preserve urgency, and apply security/compliance tags."
            ),
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
            summary=(
                "Enterprise admin reports suspicious account takeover and included employee phone numbers, "
                "internal IDs, and excerpts from a suspicious email. Recent logs show impossible travel, "
                "privilege changes, and failed admin recovery attempts. This may affect multiple users and "
                "poses immediate security and compliance risk."
            ),
        ),
        "target": {
            "queue": "security",
            "response_type": "escalate",
            "priority": "urgent",
            "must_tags": {
                "suspicious_activity",
                "sensitive",
                "priority_customer",
                "security_incident",
                "account_takeover",
                "sla_risk",
            },
            "optional_tags": {"follow_up", "policy_review"},
            "redact_pii": True,
            "must_escalate_human": True,
            "close_allowed": False,
            "policy_rules": {
                "must_preserve_urgency": True,
                "must_not_treat_as_standard_login_issue": True,
                "must_route_to_security_or_human_escalation": True,
            },
            "task_context": {
                "business_impact": "high",
                "risk_level": "critical",
                "sla_hours": 1,
            },
        },
    },
}


def list_task_ids() -> List[str]:
    return list(TASK_LIBRARY.keys())


def get_task_bundle(task_id: str) -> Dict:
    if task_id not in TASK_LIBRARY:
        raise ValueError(f"Unknown task_id: {task_id}")
    return TASK_LIBRARY[task_id]
