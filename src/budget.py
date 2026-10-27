import math
import uuid
from decimal import ROUND_CEILING, Decimal


class BudgetExceeded(RuntimeError):
    pass


def microdollars(amount):
    value = Decimal(str(amount))
    if not value.is_finite() or value < 0:
        raise ValueError("Cost must be a finite nonnegative amount.")
    return int((value * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


class Budget:
    """I reserve a conservative upper bound before sending each paid request."""

    def __init__(self, store, settings):
        self.store = store
        self.limits = {
            "anthropic": microdollars(settings.generation_budget_usd),
            "openai": microdollars(settings.openai_budget_usd),
        }

    def reserve(self, provider, maximum_usd):
        limit = self.limits[provider]
        maximum = microdollars(maximum_usd)
        if maximum == 0:
            raise ValueError("A paid request requires a positive reservation.")
        reservation = str(uuid.uuid4())

        def allocate(ledger):
            ledger = ledger or {"spent": 0, "reservations": {}}
            committed = ledger["spent"] + sum(ledger["reservations"].values())
            if committed + maximum > limit:
                raise BudgetExceeded(f"My {provider} spending allowance is exhausted.")
            ledger["reservations"][reservation] = maximum
            return ledger

        self.store.mutate("budgets", provider, allocate)
        return reservation

    def settle(self, provider, reservation, actual_usd=None):
        # I retain the full reservation when a timeout leaves billing unknown.
        def settle_ledger(ledger):
            if not ledger or reservation not in ledger["reservations"]:
                raise ValueError("Unknown or already settled reservation.")
            maximum = ledger["reservations"][reservation]
            actual = maximum if actual_usd is None else microdollars(actual_usd)
            ledger["spent"] += actual
            del ledger["reservations"][reservation]
            return ledger

        ledger = self.store.mutate("budgets", provider, settle_ledger)
        if ledger["spent"] > self.limits[provider]:
            raise BudgetExceeded("Billed cost exceeded my bound; further calls are blocked.")

    @staticmethod
    def upper_bound(input_tokens, output_tokens, input_per_million, output_per_million):
        values = (input_tokens, output_tokens, input_per_million, output_per_million)
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("Token bounds and prices must be finite and nonnegative.")
        return (
            Decimal(str(input_tokens)) * Decimal(str(input_per_million))
            + Decimal(str(output_tokens)) * Decimal(str(output_per_million))
        ) / 1_000_000
