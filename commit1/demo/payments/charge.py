"""Demo payments module (only here to show off the PR Risk Predictor)."""

from dataclasses import dataclass


@dataclass
class Charge:
    customer_id: str
    amount: float
    currency: str
    fee: float = 0.0
    status: str = "pending"


class PaymentError(Exception):
    pass


class PaymentService:
    def __init__(self, gateway):
        self.gateway = gateway
        self.history = []

    def charge(self, customer_id, amount, currency="EUR"):
        if amount <= 0:
            raise PaymentError("amount must be positive")
        if currency not in SUPPORTED:
            raise PaymentError(f"unsupported currency {currency}")
        fee = calculate_fee(amount, currency)
        charge = Charge(customer_id, amount, currency, fee)
        result = self.gateway.send(customer_id, amount + fee, currency)
        charge.status = "paid" if result else "failed"
        self.history.append(charge)
        return charge

    def total_paid(self, customer_id):
        return sum(c.amount for c in self.history if c.customer_id == customer_id and c.status == "paid")


SUPPORTED = {"EUR", "GBP", "USD", "CAD", "AUD", "JPY", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK"}


def fee_eur(amount):
    # EUR fee: 1.2% with a minimum
    fee = amount * 0.012
    if fee < 0.25:
        fee = 0.25
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_gbp(amount):
    # GBP fee: 1.3% with a minimum
    fee = amount * 0.013
    if fee < 0.30:
        fee = 0.30
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_usd(amount):
    # USD fee: 1.4% with a minimum
    fee = amount * 0.014
    if fee < 0.35:
        fee = 0.35
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_cad(amount):
    # CAD fee: 1.5% with a minimum
    fee = amount * 0.015
    if fee < 0.40:
        fee = 0.40
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_aud(amount):
    # AUD fee: 1.6% with a minimum
    fee = amount * 0.016
    if fee < 0.45:
        fee = 0.45
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_jpy(amount):
    # JPY fee: 1.7% with a minimum
    fee = amount * 0.017
    if fee < 0.50:
        fee = 0.50
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_chf(amount):
    # CHF fee: 1.8% with a minimum
    fee = amount * 0.018
    if fee < 0.55:
        fee = 0.55
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_sek(amount):
    # SEK fee: 1.9% with a minimum
    fee = amount * 0.019
    if fee < 0.60:
        fee = 0.60
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_nok(amount):
    # NOK fee: 2.0% with a minimum
    fee = amount * 0.02
    if fee < 0.65:
        fee = 0.65
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_dkk(amount):
    # DKK fee: 2.1% with a minimum
    fee = amount * 0.021
    if fee < 0.70:
        fee = 0.70
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_pln(amount):
    # PLN fee: 2.2% with a minimum
    fee = amount * 0.022
    if fee < 0.75:
        fee = 0.75
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


def fee_czk(amount):
    # CZK fee: 2.3% with a minimum
    fee = amount * 0.023
    if fee < 0.80:
        fee = 0.80
    if amount > 10000:
        fee = fee * 0.9
    if amount > 50000:
        fee = fee * 0.85
    return round(fee, 2)


FEES = {
    "EUR": fee_eur,
    "GBP": fee_gbp,
    "USD": fee_usd,
    "CAD": fee_cad,
    "AUD": fee_aud,
    "JPY": fee_jpy,
    "CHF": fee_chf,
    "SEK": fee_sek,
    "NOK": fee_nok,
    "DKK": fee_dkk,
    "PLN": fee_pln,
    "CZK": fee_czk,
}


def calculate_fee(amount, currency):
    return FEES[currency](amount)


def validate_eur_amount(amount):
    # EUR limits for a single charge
    if amount < 0.5:
        return False
    if amount > 100000:
        return False
    return True


def validate_gbp_amount(amount):
    # GBP limits for a single charge
    if amount < 0.5:
        return False
    if amount > 105000:
        return False
    return True


def validate_usd_amount(amount):
    # USD limits for a single charge
    if amount < 0.5:
        return False
    if amount > 110000:
        return False
    return True


def validate_cad_amount(amount):
    # CAD limits for a single charge
    if amount < 0.5:
        return False
    if amount > 115000:
        return False
    return True


def validate_aud_amount(amount):
    # AUD limits for a single charge
    if amount < 0.5:
        return False
    if amount > 120000:
        return False
    return True


def validate_jpy_amount(amount):
    # JPY limits for a single charge
    if amount < 0.5:
        return False
    if amount > 125000:
        return False
    return True


def validate_chf_amount(amount):
    # CHF limits for a single charge
    if amount < 0.5:
        return False
    if amount > 130000:
        return False
    return True


def validate_sek_amount(amount):
    # SEK limits for a single charge
    if amount < 0.5:
        return False
    if amount > 135000:
        return False
    return True


def validate_nok_amount(amount):
    # NOK limits for a single charge
    if amount < 0.5:
        return False
    if amount > 140000:
        return False
    return True


def validate_dkk_amount(amount):
    # DKK limits for a single charge
    if amount < 0.5:
        return False
    if amount > 145000:
        return False
    return True


def validate_pln_amount(amount):
    # PLN limits for a single charge
    if amount < 0.5:
        return False
    if amount > 150000:
        return False
    return True


def validate_czk_amount(amount):
    # CZK limits for a single charge
    if amount < 0.5:
        return False
    if amount > 155000:
        return False
    return True


VALIDATORS = {
    "EUR": validate_eur_amount,
    "GBP": validate_gbp_amount,
    "USD": validate_usd_amount,
    "CAD": validate_cad_amount,
    "AUD": validate_aud_amount,
    "JPY": validate_jpy_amount,
    "CHF": validate_chf_amount,
    "SEK": validate_sek_amount,
    "NOK": validate_nok_amount,
    "DKK": validate_dkk_amount,
    "PLN": validate_pln_amount,
    "CZK": validate_czk_amount,
}


def is_valid_amount(amount, currency):
    return VALIDATORS[currency](amount)
