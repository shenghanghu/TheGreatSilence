"""Phase 3 satellite deployment system."""

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple


SATELLITE_TYPES: Dict[str, Dict[str, object]] = {
    "basic": {
        "name": "基础中继卫星",
        "antenna_gain": 15,
        "power": 20,
        "base_cost": 300,
        "description": "低成本，基础性能",
    },
    "advanced": {
        "name": "高级中继卫星",
        "antenna_gain": 25,
        "power": 30,
        "base_cost": 600,
        "description": "高增益，适合长距离",
    },
    "laser": {
        "name": "激光通信卫星",
        "antenna_gain": 40,
        "power": 25,
        "base_cost": 1000,
        "description": "激光链路，极高带宽",
    },
}


@dataclass
class DeployResult:
    success: bool
    message: str
    cost: int = 0


class SatelliteDeployment:
    """No-slot deployment with distance-based cost."""

    def __init__(self, level_config: Dict[str, object], available_budget: int) -> None:
        dep = level_config.get("satellite_deployment", {}) or {}
        self.enabled = bool(dep.get("enabled", False))
        self.budget = max(0, int(available_budget))
        self.initial_budget = self.budget
        self.position_range = dep.get("position_range", {"x": (200, 900), "y": (120, 760)})
        self.reference_pos = tuple(dep.get("reference_pos", (120, 680)))
        self.cost_per_distance = float(dep.get("cost_per_distance", 1.8))
        self.max_satellites = int(dep.get("max_satellites", 2))
        self.deployed_satellites: List[Dict[str, object]] = []

    def _is_in_range(self, position: Tuple[float, float]) -> bool:
        x, y = position
        x_ok = self.position_range["x"][0] <= x <= self.position_range["x"][1]
        y_ok = self.position_range["y"][0] <= y <= self.position_range["y"][1]
        return bool(x_ok and y_ok)

    def get_deploy_cost(self, position: Tuple[float, float], satellite_type: str) -> int:
        sat = SATELLITE_TYPES.get(satellite_type, SATELLITE_TYPES["basic"])
        distance = float(math.hypot(position[0] - self.reference_pos[0], position[1] - self.reference_pos[1]))
        return int(sat["base_cost"] + self.cost_per_distance * distance)

    def can_deploy(self, position: Tuple[float, float], satellite_type: str) -> bool:
        if not self._is_in_range(position):
            return False
        if len(self.deployed_satellites) >= self.max_satellites:
            return False
        return self.budget >= self.get_deploy_cost(position, satellite_type)

    def deploy_satellite(self, position: Tuple[float, float], satellite_type: str) -> DeployResult:
        if not self._is_in_range(position):
            return DeployResult(False, "位置超出可部署区域")
        if len(self.deployed_satellites) >= self.max_satellites:
            return DeployResult(False, "已达到本关可部署上限")
        cost = self.get_deploy_cost(position, satellite_type)
        if self.budget < cost:
            return DeployResult(False, "预算不足", cost)

        sat_idx = len(self.deployed_satellites) + 1
        specs = SATELLITE_TYPES.get(satellite_type, SATELLITE_TYPES["basic"])
        sat = {
            "name": f"Player Sat {sat_idx}",
            "pos": (int(position[0]), int(position[1])),
            "origin_pos": (int(position[0]), int(position[1])),
            "type": "relay",
            "satellite_type": satellite_type,
            "specs": specs,
            "cost": cost,
            "is_player_satellite": True,
        }
        self.deployed_satellites.append(sat)
        self.budget -= cost
        return DeployResult(True, f"部署成功: {specs['name']}", cost)


class DynamicNetwork:
    """Apply deployed satellites into level node graph."""

    def __init__(self, level_config: Dict[str, object]) -> None:
        self.level_config = level_config

    def apply_deployment(self, deployed_satellites: List[Dict[str, object]]) -> int:
        if not deployed_satellites:
            return 0
        nodes = self.level_config.get("nodes", [])
        existing_positions = {(int(n["pos"][0]), int(n["pos"][1])) for n in nodes if "pos" in n}
        appended = 0
        for sat in deployed_satellites:
            pos_key = (int(sat["pos"][0]), int(sat["pos"][1]))
            if pos_key in existing_positions:
                continue
            nodes.append(sat)
            existing_positions.add(pos_key)
            appended += 1
        self.level_config["nodes"] = nodes
        return appended
