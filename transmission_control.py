"""Interactive controls for phase 2 operational upgrades."""

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pygame


@dataclass
class PowerSlider:
    x: int
    y: int
    width: int
    min_power: float = 10.0
    max_power: float = 70.0
    current_power: float = 30.0
    dragging: bool = False
    height: int = 26

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._set_by_mouse(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            return False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_by_mouse(event.pos[0])
            return True
        return False

    def _set_by_mouse(self, mouse_x: int) -> None:
        rel_x = mouse_x - self.x
        ratio = float(np.clip(rel_x / max(1, self.width), 0.0, 1.0))
        self.current_power = self.min_power + ratio * (self.max_power - self.min_power)

    def get_ratio(self) -> float:
        return (self.current_power - self.min_power) / max(1e-6, (self.max_power - self.min_power))


@dataclass
class SegmentedTransmission:
    data_bits: np.ndarray
    num_segments: int = 5
    segments: List[np.ndarray] = field(init=False)
    current_segment: int = 0
    results: List[Dict[str, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.segments = list(np.array_split(self.data_bits, max(1, self.num_segments)))

    def push_result(self, ber: float) -> None:
        if self.current_segment < len(self.segments):
            self.results.append({"ber": float(ber)})
            self.current_segment += 1

    def get_progress(self) -> float:
        if not self.segments:
            return 1.0
        return self.current_segment / len(self.segments)
