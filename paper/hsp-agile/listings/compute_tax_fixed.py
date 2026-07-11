def compute_tax(income: int, is_foreign: int) -> str:
    # Repaired: foreign-high surcharge checked before domestic mid.
    if income < 0:
        return "Invalid"
    if income >= 120000 and is_foreign == 1:
        return "ForeignHigh"
    if income >= 50000:
        return "DomesticMid"
    return "Low"
