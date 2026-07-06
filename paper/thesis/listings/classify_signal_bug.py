def classify_signal(level: int, threshold: int) -> str:
    # BUG: evaluates S2's guard before S1's guard
    if level >= threshold:
        return "Critical"
    if level < 0:
        return "Error"
    return "Normal"
