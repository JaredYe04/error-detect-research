def enforce_api_acl(role: int, scope: int, mfa: int) -> dict:
    """LLM candidate that looks coherent on busy ACL bands.

    Passes common guest-deny and admin-permit unit tests, but opens the
    catch-all residual (and can skip MFA step-up on high scope) --- a
    lucky-pass candidate that conjunctive Accept must refuse.
    """
    if role == 0:
        return {"permit": 0, "step_up": 0}
    # BUG 1: high-scope without MFA incorrectly permits (skips step-up).
    if role >= 3 and scope <= 3:
        return {"permit": 1, "step_up": 0}
    if role >= 1 and scope <= 1:
        return {"permit": 1, "step_up": 0}
    # BUG 2: catch-all others fail-open instead of fail-closed.
    return {"permit": 1, "step_up": 0}  # should be permit=0, step_up=0
