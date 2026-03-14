#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证阶段1/2 改动与第一关节点点击逻辑（参照 .cursor/rules 标准）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_levels():
    from levels import LevelManager
    lm = LevelManager()
    assert len(lm.levels) == 11, "应有 11 关"
    lv1 = lm.levels[0]
    assert lv1["id"] == 1 and lv1["title"] == "第一次握手"
    assert "nodes" in lv1 and len(lv1["nodes"]) == 2
    assert lv1["nodes"][0]["type"] == "src" and lv1["nodes"][1]["type"] == "dest"
    assert "tutorial_steps" in lv1 and len(lv1["tutorial_steps"]) == 4
    assert "star_thresholds" in lv1
    print("OK levels: 11 关, 第1关 nodes/tutorial_steps/star_thresholds 正确")

def test_estimate_ber_stars():
    from main import estimate_ber, estimate_stars, calculate_stars
    # 高 SNR 应得低 BER
    ber = estimate_ber(10, "BPSK", "None")
    assert 0 < ber < 0.01
    stars = estimate_stars(ber, 0.05)
    assert stars >= 3
    # 三星计算
    s = calculate_stars(0.005, {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001})
    assert s == 2
    s3 = calculate_stars(0.0005, {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001})
    assert s3 == 3
    print("OK estimate_ber / estimate_stars / calculate_stars")

def test_node_hit():
    """模拟第一关节点点击：地图内且距离<28 应命中"""
    from levels import LevelManager
    import numpy as np
    lm = LevelManager()
    level = lm.levels[0]
    nodes = level["nodes"]
    MAP_WIDTH = 1600 - 450  # 1150
    NODE_HIT_RADIUS = 28
    # 源节点 (150, 600)
    for mx, my in [(150, 600), (160, 610), (150 + 25, 600)]:
        dist_src = np.hypot(mx - nodes[0]["pos"][0], my - nodes[0]["pos"][1])
        assert dist_src < NODE_HIT_RADIUS, f"源节点 (150,600) 附近应可点: {mx},{my} dist={dist_src}"
    # 目标节点 (600, 500)
    dist_dest = np.hypot(600 - nodes[1]["pos"][0], 500 - nodes[1]["pos"][1])
    assert dist_dest == 0
    assert 600 < MAP_WIDTH and 500 < 900
    print("OK node hit: 第一关节点在 MAP_WIDTH 内且 28 半径可命中")

def test_dsp_and_music():
    from main import get_level_music
    assert get_level_music(1) == "ofeliasdream.mp3"
    assert get_level_music(11) == "dawnofchange.mp3"
    from dsp_engine import DSPEngine
    bits = DSPEngine.str_to_bits("HI")
    assert len(bits) > 0
    print("OK get_level_music + dsp")

if __name__ == "__main__":
    test_levels()
    test_estimate_ber_stars()
    test_node_hit()
    test_dsp_and_music()
    print("All checks passed.")
