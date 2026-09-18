def score_attempt(mission, decisions, elapsed, time_limit_override=None):
    """Score only server-validated decisions.

    The browser sends step/choice IDs, but points are always looked up from DB.
    """
    elapsed = max(0.0, float(elapsed or 0))
    by_step = {int(d["step_id"]): d for d in decisions if "step_id" in d}
    valid_steps = {s.id: s for s in mission.steps}
    # A mission is only complete when every step has exactly one valid choice.
    if set(by_step) != set(valid_steps) or len(by_step) != len(decisions):
        raise ValueError("Mission decisions are incomplete or invalid")

    earned = 0.0
    max_points = 0.0
    validated = []
    for step_id, step in valid_steps.items():
        choice_id = int(by_step[step_id]["choice_id"])
        choice = next((c for c in step.choices if c.id == choice_id), None)
        if choice is None:
            raise ValueError("Invalid choice for mission step")
        step_max = max((c.points for c in step.choices), default=0)
        max_points += step_max
        earned += choice.points
        validated.append({
            "step_id": step.id,
            "choice_id": choice.id,
            "points": float(choice.points),
            "hint_level": max(0, min(3, int(by_step[step_id].get("hint_level", 0) or 0))),
            "consequence": choice.consequence,
        })

    accuracy = (earned / max_points * 100) if max_points else 0
    # Time contributes up to 25%; going over the limit does not create a negative score.
    limit = max(float(time_limit_override or mission.time_limit), 1.0)
    time_factor = max(0.0, min(1.0, 1.0 - (elapsed / limit) * 0.35))
    score = max(0.0, min(100.0, accuracy * 0.75 + time_factor * 25))
    return round(score, 2), round(accuracy, 2), validated
