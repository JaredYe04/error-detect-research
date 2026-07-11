def classify_tier(score: int, floor: int) -> str:
    if score < 0:
        return "Reject"
    if score >= floor:
        return "Pass"
    # BUG: catch-all others returns wrong constant / wrong expression
    return "Pass"  # should be "Review"
