from app.graders import grade_action
from app.models import Action


def test_grade_action_deterministic():
    target = {
        "queue": "billing",
        "response_type": "reply",
        "priority": "medium",
        "must_tags": {"refund", "duplicate_charge"},
        "redact_pii": False,
        "must_escalate_human": False,
        "close_allowed": False,
    }

    action = Action(
        queue="billing",
        response_type="reply",
        priority="medium",
        tags=["refund", "duplicate_charge"],
        redact_pii=False,
        note="ok",
    )

    score1, details1 = grade_action(action, target, 1, 2)
    score2, details2 = grade_action(action, target, 1, 2)

    assert score1 == score2
    assert details1 == details2
    assert 0.0 <= score1 <= 1.0


def test_security_penalty():
    target = {
        "queue": "security",
        "response_type": "escalate",
        "priority": "urgent",
        "must_tags": {"suspicious_activity", "sensitive", "security_incident"},
        "redact_pii": True,
        "must_escalate_human": True,
        "close_allowed": False,
    }

    unsafe_action = Action(
        queue="general",
        response_type="close",
        priority="low",
        tags=[],
        redact_pii=False,
        note="unsafe",
    )

    score, _ = grade_action(unsafe_action, target, 0, 3)
    assert 0.0 <= score <= 1.0
    assert score < 0.5