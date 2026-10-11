"""Expense split math and settle-up. Pure functions; currency conversion is injected.

Expense dict fields used here:
  amount, currency, payer, and one of:
    split: [traveler_id, ...]                              equal split (default: just the payer)
    split_rule: {"type": "equal", "participants": [...]}
                {"type": "shares", "shares": {id: weight}}
                {"type": "amounts", "amounts": {id: amount}}   (in the expense's currency; must sum to amount)
  Refunds are expenses with a negative amount, split the same way as what they refund.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Any, Callable

Converter = Callable[[float, str, str], float]
CENT = Decimal("0.01")


def _cents(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _allocate(total: Decimal, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    """Split total by weights in cents; leftover cents go to the largest weights first (ties by id)."""
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("Split weights must sum to more than zero")
    raw = {k: total * w / weight_sum for k, w in weights.items()}
    shares = {k: v.quantize(CENT, rounding=ROUND_DOWN) for k, v in raw.items()}  # toward zero
    leftover = total - sum(shares.values())
    step = CENT if leftover > 0 else -CENT
    for k in sorted(weights, key=lambda k: (-weights[k], k)):
        if leftover == 0:
            break
        shares[k] += step
        leftover -= step
    return shares


def shares_for(expense: dict[str, Any]) -> dict[str, Decimal]:
    """Each participant's share of one expense, in the expense's currency."""
    total = _cents(expense["amount"])
    rule = expense.get("split_rule")
    if rule is None:
        participants = expense.get("split") or [expense["payer"]]
        return _allocate(total, {p: Decimal(1) for p in participants})
    kind = rule["type"]
    if kind == "equal":
        return _allocate(total, {p: Decimal(1) for p in rule["participants"]})
    if kind == "shares":
        return _allocate(total, {p: Decimal(str(w)) for p, w in rule["shares"].items()})
    if kind == "amounts":
        amounts = {p: _cents(v) for p, v in rule["amounts"].items()}
        if sum(amounts.values()) != total:
            raise ValueError(f"Split amounts {sum(amounts.values())} don't add up to {total}")
        return amounts
    raise ValueError(f"Unknown split rule {kind!r}")


def balances(expenses: list[dict[str, Any]], home_currency: str, convert: Converter) -> dict[str, Decimal]:
    """Net balance per traveler in home currency: positive = is owed money, negative = owes."""
    net: dict[str, Decimal] = defaultdict(Decimal)
    for expense in expenses:
        rate_amount = lambda x: _cents(convert(float(x), expense["currency"], home_currency))  # noqa: E731
        paid = rate_amount(expense["amount"])
        shares = shares_for(expense)
        net[expense["payer"]] += paid
        weights = {p: abs(s) for p, s in shares.items()}
        if not sum(weights.values()):
            continue
        for person, share in _allocate(paid, weights).items():
            net[person] -= share
    return dict(net)


def settle_up(net: dict[str, Decimal]) -> list[dict[str, Any]]:
    """Fewest-transfers-ish greedy settle-up: largest debtor pays largest creditor."""
    debtors = sorted(((p, -b) for p, b in net.items() if b < 0), key=lambda x: (-x[1], x[0]))
    creditors = sorted(((p, b) for p, b in net.items() if b > 0), key=lambda x: (-x[1], x[0]))
    transfers, i, j = [], 0, 0
    debtors, creditors = [list(d) for d in debtors], [list(c) for c in creditors]
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i][1], creditors[j][1])
        if amount > 0:
            transfers.append({"from": debtors[i][0], "to": creditors[j][0], "amount": float(amount)})
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1
    return transfers
