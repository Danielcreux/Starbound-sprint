"""Frame-rate-independent scalar movement helpers."""


def approach(value: float, target: float, amount: float) -> float:
    if value < target:
        return min(value + amount, target)
    return max(value - amount, target)
