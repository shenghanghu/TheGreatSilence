"""Pre-transmission causal chain animation (scheme 2)."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pygame


@dataclass
class ChainNode:
    key: str
    label: str
    value_text: str
    effect_text: str
    color: Tuple[int, int, int]
    x: int
    y: int
    alpha: int = 0


class CausalChainAnimation:
    def __init__(self, config: Dict[str, object], window_size: Tuple[int, int]) -> None:
        self.config = config
        self.window_size = window_size
        self.state = "idle"
        self.start_ms = 0
        self.duration_s = 2.6
        self._nodes: List[ChainNode] = []
        self._build_chain_nodes()

    def _build_chain_nodes(self) -> None:
        w, h = self.window_size
        y = h // 2 - 30
        x0 = w // 2 - 360
        spacing = 180

        base_snr = float(self.config.get("base_snr", 8.0))
        mod = str(self.config.get("modulation", "BPSK"))
        coding = str(self.config.get("coding", "None"))
        weather = str(self.config.get("weather", "clear"))
        protocol = str(self.config.get("protocol", "udp")).upper()

        mod_effect = float(self.config.get("mod_effect", 0.0))
        code_effect = float(self.config.get("code_effect", 0.0))
        weather_effect = float(self.config.get("weather_effect", 0.0))
        proto_effect = float(self.config.get("protocol_effect", 1.0))
        final_snr = float(self.config.get("final_snr", base_snr + mod_effect + code_effect + weather_effect))
        success_rate = float(self.config.get("success_rate", 0.5))

        self._nodes = [
            ChainNode("base", "基础SNR", f"{base_snr:.1f} dB", "", (100, 100, 120), x0, y),
            ChainNode("mod", mod, f"{base_snr + mod_effect:.1f} dB", f"{mod_effect:+.1f} dB", (0, 150, 210), x0 + spacing, y),
            ChainNode("coding", coding, f"{base_snr + mod_effect + code_effect:.1f} dB", f"{code_effect:+.1f} dB", (0, 180, 100), x0 + spacing * 2, y),
            ChainNode("weather", weather, f"{final_snr:.1f} dB", f"{weather_effect:+.1f} dB", (200, 120, 30), x0 + spacing * 3, y),
            ChainNode("final", f"{protocol}", f"成功率 {success_rate * 100:.0f}%", f"BER x{proto_effect:.2f}", (220, 180, 70), x0 + spacing * 4, y),
        ]

    def start(self) -> None:
        self.state = "playing"
        self.start_ms = pygame.time.get_ticks()

    def is_playing(self) -> bool:
        return self.state == "playing"

    def is_finished(self) -> bool:
        return self.state == "finished"

    def update(self) -> None:
        if self.state != "playing":
            return
        elapsed = (pygame.time.get_ticks() - self.start_ms) / 1000.0
        for idx, node in enumerate(self._nodes):
            t0 = 0.2 + idx * 0.35
            if elapsed < t0:
                node.alpha = 0
            else:
                progress = min((elapsed - t0) / 0.25, 1.0)
                node.alpha = int(255 * progress)
        if elapsed >= self.duration_s:
            self.state = "finished"

    def draw(self, surface, font, label_font, header_font) -> None:
        if self.state == "idle":
            return
        w, h = self.window_size
        elapsed = (pygame.time.get_ticks() - self.start_ms) / 1000.0 if self.start_ms else 0.0
        fade = min(1.0, elapsed / 0.25)
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(170 * fade)))
        surface.blit(overlay, (0, 0))

        title = header_font.render("发射因果链分析", True, (180, 220, 255))
        surface.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 180))

        for i, node in enumerate(self._nodes):
            if node.alpha <= 0:
                continue
            self._draw_node(surface, node, label_font)
            if i > 0 and self._nodes[i - 1].alpha > 160:
                self._draw_arrow(surface, self._nodes[i - 1], node)

        if elapsed > 2.0:
            tip = font.render("链路分析完成，准备发射...", True, (220, 220, 220))
            surface.blit(tip, (w // 2 - tip.get_width() // 2, h // 2 + 120))

    def _draw_node(self, surface, node: ChainNode, label_font) -> None:
        circle = pygame.Surface((120, 120), pygame.SRCALPHA)
        c = (*node.color, node.alpha)
        pygame.draw.circle(circle, c, (60, 60), 48)
        pygame.draw.circle(circle, (255, 255, 255, node.alpha), (60, 60), 48, 2)
        surface.blit(circle, (node.x - 60, node.y - 60))

        label = label_font.render(node.label, True, (245, 245, 245))
        value = label_font.render(node.value_text, True, (255, 255, 255))
        effect_color = (120, 255, 140) if node.effect_text.startswith("+") else (255, 160, 130)
        effect = label_font.render(node.effect_text, True, effect_color)

        surface.blit(label, (node.x - label.get_width() // 2, node.y - 20))
        surface.blit(value, (node.x - value.get_width() // 2, node.y))
        if node.effect_text:
            surface.blit(effect, (node.x - effect.get_width() // 2, node.y + 20))

    def _draw_arrow(self, surface, node1: ChainNode, node2: ChainNode) -> None:
        x1 = node1.x + 52
        x2 = node2.x - 52
        y = node1.y
        pygame.draw.line(surface, (80, 170, 255), (x1, y), (x2, y), 3)
        pygame.draw.polygon(surface, (80, 170, 255), [(x2, y), (x2 - 12, y - 7), (x2 - 12, y + 7)])
