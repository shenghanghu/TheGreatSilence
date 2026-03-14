"""Protocol effects and selection helpers."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ProtocolInfo:
    name: str
    cost: int
    description: str
    speed_boost: float
    ber_multiplier: float
    energy_multiplier: float
    unlock_level: int = 1


class ProtocolSystem:
    def __init__(self) -> None:
        self.protocols: Dict[str, ProtocolInfo] = {
            "udp": ProtocolInfo("UDP", 10, "快速但不可靠", 1.5, 1.2, 0.8, 1),
            "tcp": ProtocolInfo("TCP", 20, "可靠但较慢", 0.7, 0.5, 1.3, 2),
            "sctp": ProtocolInfo("SCTP", 30, "平衡性能", 1.2, 0.8, 1.1, 4),
            "quic": ProtocolInfo("QUIC", 40, "现代高性能协议", 1.8, 0.9, 1.2, 8),
        }

    def get_protocol_info(self, protocol_id: str) -> ProtocolInfo:
        return self.protocols.get(protocol_id, self.protocols["udp"])

    def get_available_protocols(self, level_id: int) -> Dict[str, ProtocolInfo]:
        return {
            proto_id: proto
            for proto_id, proto in self.protocols.items()
            if level_id >= proto.unlock_level
        }

    def apply_ber_effect(self, protocol_id: str, ber_value: float) -> float:
        proto = self.get_protocol_info(protocol_id)
        ber = float(ber_value) * proto.ber_multiplier
        return max(1e-7, min(0.5, ber))

    def apply_energy_effect(self, protocol_id: str, energy_cost: float) -> float:
        proto = self.get_protocol_info(protocol_id)
        return float(energy_cost) * proto.energy_multiplier
