from app.env import SupportTriageEnv
from app.models import Action


def test_reset_and_state():
    env = SupportTriageEnv()
    reset_response = env.reset("easy_refund_request")
    assert reset_response.observation.task.task_id == "easy_refund_request"

    state = env.state()
    assert state.task_id == "easy_refund_request"
    assert state.done is False
    assert state.step_index == 0


def test_multi_step_episode():
    env = SupportTriageEnv()
    env.reset("medium_login_locked")

    result1 = env.step(
        Action(
            queue="account",
            response_type="request_info",
            priority="high",
            tags=["login_issue", "verification_required"],
            redact_pii=False,
            note="request more info",
        )
    )
    assert result1.done is False
    assert 0.0 <= result1.reward.score <= 1.0

    result2 = env.step(
        Action(
            queue="account",
            response_type="request_info",
            priority="high",
            tags=["login_issue", "verification_required", "follow_up"],
            redact_pii=False,
            note="follow up",
        )
    )
    assert result2.done is True
    assert 0.0 <= result2.reward.score <= 1.0