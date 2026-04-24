from models.reward import Reward
from env.state import EnvState


def compute_reward(action_text: str, state: EnvState) -> Reward:
    score = 0.0
    feedback_parts = []

    action_lower = action_text.lower()

    # -------------------------
    # 1. Diagnosis Check
    # -------------------------
    if any(keyword in action_lower for keyword in state.diagnosis_keywords):
        score += 0.4
        feedback_parts.append("Correct diagnosis")

    # -------------------------
    # 2. Solution Check
    # -------------------------
    # Pattern-based matching (clean design)
    for pattern in state.solution_patterns:
        if all(word in action_lower for word in pattern):
            score += 0.5
            feedback_parts.append("Correct solution")
            break
    if any(keyword in action_lower for keyword in state.solution_keywords):
        score += 0.5
        feedback_parts.append("Correct solution")

# Extra flexible matching
    elif "kill" in action_lower and "process" in action_lower:
        score += 0.5
        feedback_parts.append("Correct solution (flex match)")
    elif "change" in action_lower and "port" in action_lower:
        score += 0.5
    feedback_parts.append("Correct solution (flex match)")

    # -------------------------
    # 3. Explanation Quality
    # -------------------------
    if len(action_text.split()) > 6:
        score += 0.1
        feedback_parts.append("Good explanation")

    # -------------------------
    # 4. Penalty: Irrelevant / weak response
    # -------------------------
    if len(action_text.strip()) < 5:
        score -= 0.2
        feedback_parts.append("Too short / low effort")

    # -------------------------
    # Clamp score to [0, 1]
    # -------------------------
    score = max(0.0, min(score, 1.0))

    if not feedback_parts:
        feedback_parts.append("No meaningful progress")

    return Reward(
        score=score,
        feedback=", ".join(feedback_parts)
    )