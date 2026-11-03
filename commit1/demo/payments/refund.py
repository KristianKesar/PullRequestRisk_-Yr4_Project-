"""Demo refunds (only here to show off the PR Risk Predictor)."""

from .charge import PaymentError


def refund(service, charge, reason=None):
    if charge.status != "paid":
        raise PaymentError("can only refund paid charges")
    ok = service.gateway.refund(charge.customer_id, charge.amount, charge.currency)
    charge.status = "refunded" if ok else charge.status
    return {"ok": ok, "reason": reason or "not given"}


def refund_duplicate(service, charge):
    return refund(service, charge, reason="duplicate")


def refund_fraud(service, charge):
    return refund(service, charge, reason="fraud")


def refund_requested(service, charge):
    return refund(service, charge, reason="requested")


def refund_damaged(service, charge):
    return refund(service, charge, reason="damaged")


def refund_late(service, charge):
    return refund(service, charge, reason="late")


def refund_wrong_item(service, charge):
    return refund(service, charge, reason="wrong_item")


def refund_cancelled(service, charge):
    return refund(service, charge, reason="cancelled")


def refund_other(service, charge):
    return refund(service, charge, reason="other")


def partial_refund(service, charge, amount):
    if amount <= 0 or amount > charge.amount:
        raise PaymentError("bad refund amount")
    ok = service.gateway.refund(charge.customer_id, amount, charge.currency)
    if ok:
        charge.amount -= amount
    return ok
