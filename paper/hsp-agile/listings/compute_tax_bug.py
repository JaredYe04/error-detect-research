def compute_tax(income: int, is_foreign: int) -> str:
    # BUG: evaluates the mid-bracket guard before the foreign-high
    # surcharge. On (150000, 1) both guards hold; FSF first-match
    # requires "ForeignHigh", but this candidate returns "DomesticMid".
    if income < 0:
        return "Invalid"
    if income >= 50000:
        return "DomesticMid"
    if income >= 120000 and is_foreign == 1:
        return "ForeignHigh"
    return "Low"
