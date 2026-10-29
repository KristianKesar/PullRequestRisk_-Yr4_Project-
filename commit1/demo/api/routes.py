"""Demo API routes (only here to show off the PR Risk Predictor)."""


def charge_route(service, request):
    body = request.json()
    charge = service.charge(body["customer_id"], body["amount"], body.get("currency", "EUR"))
    return {"status": charge.status, "fee": charge.fee}


def refund_route(service, charges, request):
    body = request.json()
    charge = charges[body["charge_id"]]
    from demo.payments.refund import refund

    return refund(service, charge, body.get("reason"))


def total_route(service, request):
    return {"total": service.total_paid(request.args["customer_id"])}
