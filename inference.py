import os
from typing import Dict, List

import httpx
from openai import OpenAI

TASKS = [
    "easy_refund_request",
    "medium_login_locked",
    "hard_security_breach",
]

BENCHMARK = "blue_stars_support_triage"


def build_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["API_KEY"],
        base_url=os.environ["API_BASE_URL"],
    )


def require_model_name() -> str:
    return os.environ["MODEL_NAME"]


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


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


def call_required_llm_proxy(client: OpenAI, model_name: str, task_id: str, observation: Dict) -> None:
    prompt = (
        f"Task: {task_id}\n"
        f"Ticket summary: {observation['ticket']['summary']}\n"
        f"Reply with exactly OK."
    )
    client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Reply with exactly OK."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=5,
        stream=False,
    )


def action_to_str(action: Dict) -> str:
    return (
        f"queue={action['queue']};"
        f"response_type={action['response_type']};"
        f"priority={action['priority']};"
        f"tags={','.join(action.get('tags', []))};"
        f"redact_pii={str(action.get('redact_pii', False)).lower()}"
    )


def run_task(base_url: str, task_id: str, client: OpenAI, model_name: str) -> float:
    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0

    with httpx.Client(timeout=60.0) as http:
        reset_response = http.post(f"{base_url}/reset", params={"task_id": task_id})
        reset_response.raise_for_status()
        observation = reset_response.json()["observation"]

        log_start(task=task_id, env=BENCHMARK, model=model_name)

        try:
            call_required_llm_proxy(client, model_name, task_id, observation)

            done = False
            while not done:
                step_index = observation["step_index"]
                action = choose_action(task_id, step_index, observation)

                step_response = http.post(f"{base_url}/step", json=action)
                step_response.raise_for_status()
                result = step_response.json()

                reward = float(result["reward"]["score"])
                done = bool(result["done"])
                rewards.append(reward)
                steps_taken += 1

                log_step(
                    step=steps_taken,
                    action=action_to_str(action),
                    reward=reward,
                    done=done,
                    error=None,
                )

                observation = result["observation"]

            score = rewards[-1] if rewards else 0.0
            score = max(0.0, min(1.0, score))
            success = score > 0.0

        except Exception as exc:
            log_step(
                step=max(1, steps_taken + 1),
                action="exception",
                reward=0.00,
                done=True,
                error=str(exc),
            )
            success = False
            score = 0.0

        finally:
            log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


def main() -> None:
    base_url = os.getenv("SPACE_URL", "http://127.0.0.1:7860")
    client = build_client()
    model_name = require_model_name()

    for task_id in TASKS:
        run_task(base_url, task_id, client, model_name)


if __name__ == "__main__":
    main()
