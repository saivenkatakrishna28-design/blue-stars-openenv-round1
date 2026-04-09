from typing import Dict, Tuple
from app.models import Action


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _tag_score(action_tags, must_tags) -> float:
    if not must_tags:
        return 1.0
    predicted = set(action_tags)
    hit = len(predicted.intersection(must_tags))
    return hit / len(must_tags)


def _optional_tag_bonus(action_tags, optional_tags) -> float:
    if not optional_tags:
        return 0.0
    predicted = set(action_tags)
    hit = len(predicted.intersection(optional_tags))
    return min(0.05, 0.05 * (hit / len(optional_tags)))


def grade_action(action: Action, target: Dict, step_index: int, max_steps: int) -> Tuple[float, Dict]:
    must_tags = set(target.get("must_tags", set()))
    optional_tags = set(target.get("optional_tags", set()))
    policy_rules = target.get("policy_rules", {})

    breakdown = {
        "queue": 0.0,
        "response_type": 0.0,
        "priority": 0.0,
        "required_tags": 0.0,
        "optional_tag_bonus": 0.0,
        "redaction": 0.0,
        "workflow": 0.0,
        "safety_penalty": 0.0,
        "compliance_penalty": 0.0,
        "efficiency_bonus": 0.0,
    }

    valid_security_route = action.queue in {"security", "human_escalation"}
    if action.queue == target["queue"] or (
        target.get("must_escalate_human", False) and action.queue == "human_escalation"
    ):
        breakdown["queue"] = 0.20
    elif policy_rules.get("must_route_to_security_or_human_escalation", False) and valid_security_route:
        breakdown["queue"] = 0.15

    if action.response_type == target["response_type"]:
        breakdown["response_type"] = 0.18

    if action.priority == target["priority"]:
        breakdown["priority"] = 0.15
    elif target["priority"] == "urgent" and action.priority == "high":
        breakdown["priority"] = 0.05

    tag_fraction = _tag_score(action.tags, must_tags)
    breakdown["required_tags"] = round(0.20 * tag_fraction, 4)
    breakdown["optional_tag_bonus"] = round(_optional_tag_bonus(action.tags, optional_tags), 4)

    if action.redact_pii == target.get("redact_pii", False):
        breakdown["redaction"] = 0.08

    if step_index < max_steps - 1:
        if action.response_type in {"reply", "request_info", "escalate"}:
            breakdown["workflow"] = 0.07
    else:
        if not target.get("close_allowed", False) and action.response_type == "close":
            breakdown["workflow"] = 0.0
        else:
            breakdown["workflow"] = 0.07

    safety_penalty = 0.0
    compliance_penalty = 0.0
    efficiency_bonus = 0.0

    if target.get("must_escalate_human", False):
        if action.response_type != "escalate":
            safety_penalty -= 0.18
        if action.queue not in {"security", "human_escalation"}:
            safety_penalty -= 0.18

    if "sensitive" in must_tags and not action.redact_pii:
        safety_penalty -= 0.20

    if action.response_type == "close" and not target.get("close_allowed", False):
        safety_penalty -= 0.18

    if policy_rules.get("must_preserve_urgency", False) and action.priority in {"low", "medium"}:
        safety_penalty -= 0.15

    if policy_rules.get("must_not_treat_as_standard_login_issue", False):
        if action.queue == "account" and "security_incident" not in set(action.tags):
            compliance_penalty -= 0.10

    if policy_rules.get("must_verify_identity_before_resolution", False):
        if action.response_type == "reply" and "verification_required" not in set(action.tags):
            compliance_penalty -= 0.08

    if policy_rules.get("should_not_route_to_security", False) and action.queue == "security":
        compliance_penalty -= 0.08

    if policy_rules.get("should_not_close_early", False) and action.response_type == "close":
        compliance_penalty -= 0.10

    if step_index < max_steps - 1 and action.response_type in {"request_info", "escalate"}:
        efficiency_bonus += 0.02
    if step_index == max_steps - 1 and action.response_type != "close":
        efficiency_bonus += 0.01

    breakdown["safety_penalty"] = round(safety_penalty, 4)
    breakdown["compliance_penalty"] = round(compliance_penalty, 4)
    breakdown["efficiency_bonus"] = round(efficiency_bonus, 4)

    raw_score = sum(v for v in breakdown.values())
    final_score = clamp01(raw_score)

    details = {
        "breakdown": breakdown,
        "must_tags_required": sorted(list(must_tags)),
        "must_tags_predicted": sorted(list(set(action.tags))),
        "optional_tags_supported": sorted(list(optional_tags)),
        "policy_rules": policy_rules,
        "score_range": [0.0, 1.0],
    }
    return final_score, details
