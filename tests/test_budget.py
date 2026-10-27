from concurrent.futures import ThreadPoolExecutor

import pytest

from src.budget import Budget, BudgetExceeded, microdollars
from src.config import Settings
from src.store import SQLiteStore


@pytest.fixture
def budget(tmp_path):
    return Budget(SQLiteStore(tmp_path / "budget.sqlite3"), Settings(_env_file=None))


def test_concurrent_reservations_cannot_overspend(budget):
    def reserve(_):
        try:
            return budget.reserve("anthropic", 0.5)
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations = list(pool.map(reserve, range(20)))
    assert len([r for r in reservations if r]) == 5


def test_unknown_billing_retains_full_cost_across_restart(budget):
    reservation = budget.reserve("anthropic", 2.5)
    budget.settle("anthropic", reservation)
    restored = Budget(SQLiteStore(budget.store.path), Settings(_env_file=None))
    with pytest.raises(BudgetExceeded):
        restored.reserve("anthropic", 0.000001)
    assert restored.reserve("openai", 5)


def test_settlement_releases_only_unused_bound(budget):
    reservation = budget.reserve("anthropic", 2)
    budget.settle("anthropic", reservation, 1)
    assert budget.reserve("anthropic", 1.5)
    with pytest.raises(BudgetExceeded):
        budget.reserve("anthropic", 0.000001)
    with pytest.raises(ValueError, match="already settled"):
        budget.settle("anthropic", reservation, 0)


def test_underestimated_bill_is_recorded_and_blocks_further_calls(budget):
    reservation = budget.reserve("anthropic", 1)
    with pytest.raises(BudgetExceeded):
        budget.settle("anthropic", reservation, 3)
    assert budget.store.get("budgets", "anthropic")["spent"] == 3_000_000
    with pytest.raises(BudgetExceeded):
        budget.reserve("anthropic", 0.1)


@pytest.mark.parametrize("amount", [-1, "NaN", "Infinity"])
def test_invalid_cost_rejected(amount):
    with pytest.raises(ValueError):
        microdollars(amount)


def test_conservative_rounding_and_token_cost():
    assert microdollars("0.0000001") == 1
    assert microdollars(Budget.upper_bound(1000, 100, 3, 15)) == 4500
