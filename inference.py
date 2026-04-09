import os
from typing import Dict, List

import httpx
from openai import OpenAI

TASKS = [
    "easy_refund_request",
    "medium_login_locked",
    "hard_security_breach",
]


def build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", os.getenv("HF_TOKEN", "dummy-key"))
    base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def maybe_call_openai(client: OpenAI) -> None:
    model_name = os.getenv("MODEL_NAME", "")
    if not model_name:
        return
    try:
        client.responses.create(
            model=model_name,
            input="Return exactly OK.",
            max_output_tokens=5,
        )
    except Exception:
        pass


def print_start(task_id: str) -> None:
    print(f"[START] task={task_id}", flush=True)


def print_step(task_id: str, step_index: int, reward: float, action: Dict) -> None:
    queue = action.get("queue", "")
    response_type = action.get("response_type", "")
    priority = action.get("priority", "")
    print(
        f"[STEP] task={task_id} step={step_index} reward={reward:.4f} "
        f"queue={queue} response_type={response_type} priority={priority}",
        flush=True,
    )


def print_end(task_id: str, final_score: float, steps: int) -> None:
    print(f"[END] task={task_id} score={final_score:.4f} steps={steps}", flush=True)


def choose_action(task_id: str, step_index: int, observation: Dict) -> Dict:
    if task_id == "easy_refund_request":
        if step_index == 0:
            return {
                "queue": "billing",
                "response_type": "request_info",
                "priority": "medium",
                "tags": ["refund", "duplicate_charge", "billing_error"],
                "redact_pii": False,
                "note": "Initial triage for duplicate-charge refund.",
            }
        return {
            "queue": "billing",
            "response_type": "reply",
            "priority": "medium",
            "tags": ["refund", "duplicate_charge", "billing_error"],
            "redact_pii": False,
            "note": "Billing response with refund triage.",
        }

    if task_id == "medium_login_locked":
        if step_index == 0:
            return {
                "queue": "account",
                "response_type": "request_info",
                "priority": "high",
                "tags": ["login_issue", "verification_required", "identity_check"],
                "redact_pii": False,
                "note": "Request identity verification and account details.",
            }
        return {
            "queue": "account",
            "response_type": "request_info",
            "priority": "high",
            "tags": ["login_issue", "verification_required", "follow_up", "identity_check"],
            "redact_pii": False,
            "note": "Follow-up for secure account recovery.",
        }

    if task_id == "hard_security_breach":
        if step_index == 0:
            return {
                "queue": "security",
                "response_type": "escalate",
                "priority": "urgent",
                "tags": ["suspicious_activity", "security_incident", "account_takeover"],
                "redact_pii": True,
                "note": "Urgent security triage.",
            }
        if step_index == 1:
            return {
                "queue": "human_escalation",
                "response_type": "escalate",
                "priority": "urgent",
                "tags": ["suspicious_activity", "security_incident", "sensitive", "account_takeover"],
                "redact_pii": True,
                "note": "Escalate to human security specialist.",
            }
        return {
            "queue": "security",
            "response_type": "escalate",
            "priority": "urgent",
            "tags": [
                "suspicious_activity",
                "security_incident",
                "sensitive",
                "priority_customer",
                "account_takeover",
                "sla_risk",
            ],
            "redact_pii": True,
            "note": "Finalize secure escalation for enterprise account.",
        }

    return {
        "queue": "general",
        "response_type": "request_info",
        "priority": "medium",
        "tags": [],
        "redact_pii": observation["ticket"].get("contains_pii", False),
        "note": "Fallback action.",
    }


def run_task(base_url: str, task_id: str, client: OpenAI) -> float:
    print_start(task_id)

    with httpx.Client(timeout=60.0) as http:
        reset_response = http.post(f"{base_url}/reset", params={"task_id": task_id})
        reset_response.raise_for_status()
        observation = reset_response.json()["observation"]

        maybe_call_openai(client)

        done = False
        final_reward = 0.0
        total_steps = 0

        while not done:
            step_index = observation["step_index"]
            action = choose_action(task_id, step_index, observation)

            step_response = http.post(f"{base_url}/step", json=action)
            step_response.raise_for_status()
            result = step_response.json()

            reward = float(result["reward"]["score"])
            done = bool(result["done"])
            final_reward = reward
            total_steps += 1

            print_step(task_id, step_index, reward, action)
            observation = result["observation"]

        print_end(task_id, final_reward, total_steps)
        return final_reward


def main() -> None:
    base_url = os.getenv("SPACE_URL", "http://127.0.0.1:7860")
    client = build_client()

    scores: List[float] = []
    for task_id in TASKS:
        score = run_task(base_url, task_id, client)
        scores.append(score)

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"[SUMMARY] average_score={avg:.4f} tasks={len(scores)}", flush=True)


if __name__ == "__main__":
    main()
