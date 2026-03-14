"""Budget and transmission cost helpers for phase 1."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


STAR_REWARDS: Dict[int, int] = {
    1: 100,
    2: 250,
    3: 500,
}


COST_TABLE: Dict[str, int] = {
    "transmission_base": 50,
    "power_multiplier": 2,
    "protocol_udp": 10,
    "protocol_tcp": 20,
    "protocol_sctp": 30,
    "protocol_quic": 40,
    "retransmission": 30,
}


def calculate_level_reward(stars: int, level_difficulty: float = 1.0) -> int:
    base_reward = STAR_REWARDS.get(stars, 0)
    return int(base_reward * max(0.1, level_difficulty))


def calculate_transmission_cost(power_dbm: float, protocol: str = "udp") -> int:
    base = COST_TABLE["transmission_base"]
    power_delta = max(0.0, float(power_dbm) - 30.0)
    power_cost = int(power_delta * COST_TABLE["power_multiplier"])
    protocol_cost = COST_TABLE.get(f"protocol_{protocol}", 0)
    return base + power_cost + protocol_cost


@dataclass
class BudgetManager:
    total_budget: int = 1000
    current_budget: int = 1000
    spent_this_level: int = 0
    transaction_history: List[Dict[str, object]] = field(default_factory=list)

    def __init__(self, initial_budget: int = 1000) -> None:
        safe_budget = max(0, int(initial_budget))
        self.total_budget = safe_budget
        self.current_budget = safe_budget
        self.spent_this_level = 0
        self.transaction_history = []

    def can_afford(self, cost: int) -> bool:
        return self.current_budget >= max(0, int(cost))

    def spend(self, cost: int, description: str = "") -> Tuple[bool, str]:
        safe_cost = max(0, int(cost))
        if not self.can_afford(safe_cost):
            return False, "预算不足"

        self.current_budget -= safe_cost
        self.spent_this_level += safe_cost
        self.transaction_history.append(
            {
                "type": "spend",
                "amount": safe_cost,
                "description": description,
                "balance": self.current_budget,
            }
        )
        return True, f"消耗 {safe_cost} 预算"

    def earn(self, amount: int, description: str = "") -> Tuple[bool, str]:
        safe_amount = max(0, int(amount))
        self.current_budget += safe_amount
        self.total_budget = max(self.total_budget, self.current_budget)
        self.transaction_history.append(
            {
                "type": "earn",
                "amount": safe_amount,
                "description": description,
                "balance": self.current_budget,
            }
        )
        return True, f"获得 {safe_amount} 预算"

    def reset_level(self) -> None:
        self.spent_this_level = 0
