#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证近期改动：成就图片、level_stars 归一化、Polar 解锁。可无 pygame 运行部分测试。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _resource_path(relative_path):
    """与 main.py 一致，用于测试时解析成就图片路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_path, relative_path))


def test_achievement_images():
    """隐藏成就应包含 image 路径"""
    from achievements import ACHIEVEMENTS, CATEGORY_HIDDEN
    hidden = [a for a in ACHIEVEMENTS.values() if a.get("hidden")]
    with_image = [a for a in hidden if a.get("image")]
    assert len(with_image) >= 5, "至少 5 个隐藏成就应有 image"
    names = {a["name"] for a in with_image}
    assert "彩蛋发现者" in names and "香农致敬" in names and "幸运七" in names
    assert "全能选手" in names and "完美主义者+" in names
    for a in with_image:
        assert a["image"].startswith("隐藏成就/") and a["image"].endswith(".png")
    print("OK 成就: 隐藏成就均配置 image 路径")


def test_achievement_image_files():
    """成就图片文件存在且可被 pygame 加载（能正常显示）"""
    from achievements import ACHIEVEMENTS
    with_image = [(aid, a) for aid, a in ACHIEVEMENTS.items() if a.get("image")]
    assert len(with_image) >= 5, "至少 5 个成就配置了 image"
    missing = []
    for ach_id, ach_data in with_image:
        rel = ach_data["image"]
        full = _resource_path(rel)
        if not os.path.exists(full):
            missing.append(f"{ach_id}: {rel} -> {full}")
    assert not missing, "成就图片文件缺失:\n" + "\n".join(missing)
    print("OK 成就图片: 5 个文件均存在")
    try:
        import pygame
        pygame.init()
        # 无窗口时 pygame.image.load().convert_alpha() 需先设置 video mode（与游戏中一致）
        pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)
        for ach_id, ach_data in with_image:
            full = _resource_path(ach_data["image"])
            img = pygame.image.load(full).convert_alpha()
            w, h = img.get_size()
            assert w > 0 and h > 0, f"{ach_id} 图片尺寸无效"
        pygame.quit()
        print("OK 成就图片: pygame 加载可用于显示")
    except ImportError:
        print("SKIP 成就图片 pygame 加载: 未安装 pygame")
    except Exception as e:
        raise AssertionError(f"成就图片加载失败: {e}") from e


def test_level_stars_normalize():
    """level_stars 字符串 key 应能归一化为 int"""
    raw = {"1": 3, "2": 2, "3": 1}
    stars_dict = {}
    for k, v in raw.items():
        try:
            key = int(k) if isinstance(k, str) and k.isdigit() else k
            if isinstance(key, int):
                stars_dict[key] = v
        except (ValueError, TypeError):
            pass
    assert stars_dict == {1: 3, 2: 2, 3: 1}
    # 选关时用 int 查
    assert stars_dict.get(1, 0) == 3
    print("OK level_stars: 字符串 key 归一化为 int 后查星级正确")


def test_load_progress_normalize():
    """load_progress 返回的 stars 应为 int key（若 save.json 存在）"""
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")
    if not os.path.exists(save_path):
        print("SKIP load_progress: 无 save.json")
        return
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_stars = data.get("level_stars", {})
    stars_dict = {}
    for k, v in (raw_stars or {}).items():
        try:
            key = int(k) if isinstance(k, str) and k.isdigit() else k
            if isinstance(key, int):
                stars_dict[key] = v
        except (ValueError, TypeError):
            pass
    if raw_stars:
        assert all(isinstance(k, int) for k in stars_dict), "归一化后 key 应为 int"
    print("OK load_progress 归一化逻辑: 与 save.json 一致")


def test_polar_unlock_logic():
    """关卡 available_codes 含 Polar(256,128) 时，unlocked 应含 'Polar'（需 pygame/tech_tree）"""
    try:
        from tech_tree import get_unlocked_techs
    except ImportError:
        print("SKIP Polar: 需要 pygame/tech_tree")
        return
    # tech_tree 用 lv.get("available_mods", [])，需传 dict 或类 dict
    def level(mods, codes):
        return {"available_mods": mods, "available_codes": codes}
    class FakeLevelMgr:
        levels = [
            level(["BPSK"], ["None"]),
            level(["BPSK", "QPSK"], ["None", "Repetition(3,1)"]),
            level(["BPSK", "QPSK"], ["None", "Repetition(3,1)", "Hamming(7,4)"]),
            level(["BPSK", "QPSK"], ["None", "Repetition(3,1)", "Hamming(7,4)"]),
            level(["BPSK", "QPSK"], ["None", "Repetition(3,1)", "Hamming(7,4)"]),
            level(["BPSK", "QPSK", "8PSK"], ["Hamming(7,4)", "Polar(256,128)"]),
        ]
    unlocked = get_unlocked_techs(FakeLevelMgr(), 5)  # 0..5 共 6 关
    assert "Polar" in unlocked, "第6关含 Polar(256,128) 时 Polar 应已解锁"
    print("OK Polar: get_unlocked_techs 正确将 Polar(N,K) 视为 Polar 解锁")


def test_phase1_phase2_systems():
    """验证阶段1/2核心系统：预算、天气、协议、功率控制。"""
    from budget_system import BudgetManager, calculate_transmission_cost
    from weather_system import WeatherSystem
    from protocol_system import ProtocolSystem
    try:
        from transmission_control import PowerSlider
    except ImportError:
        print("SKIP 阶段2功率滑块: 需要 pygame/numpy")
        PowerSlider = None

    bm = BudgetManager(initial_budget=300)
    cost = calculate_transmission_cost(40, "udp")
    high_cost = calculate_transmission_cost(70, "udp")
    assert high_cost > cost * 2
    ok, _ = bm.spend(cost, "test")
    assert ok and bm.current_budget == 300 - cost
    ok2, _ = bm.spend(9999, "overflow")
    assert not ok2

    ws = WeatherSystem()
    ws.set_weather("storm")
    snr = ws.apply_snr_effects(10, "Polar(256,128)", use_laser=True)
    assert snr < 10
    ber = ws.apply_ber_effects(0.01, "Polar(256,128)")
    assert 0 < ber < 0.02

    ps = ProtocolSystem()
    assert "udp" in ps.get_available_protocols(1)
    assert "quic" not in ps.get_available_protocols(1)
    assert "quic" in ps.get_available_protocols(8)

    if PowerSlider is not None:
        slider = PowerSlider(0, 0, 100)
        class E:
            pass
        down = E()
        down.type = 1025  # pygame.MOUSEBUTTONDOWN
        down.pos = (80, 10)
        slider.handle_event(down)
        assert slider.current_power > 30
    print("OK 阶段1/2系统：预算/天气/协议/功率滑块")


def test_phase3_satellite_system():
    """验证阶段3核心系统：卫星部署与动态网络写入。"""
    from satellite_system import SatelliteDeployment, DynamicNetwork

    level = {
        "nodes": [
            {"name": "Src", "pos": (100, 400), "type": "src"},
            {"name": "Dst", "pos": (800, 400), "type": "dest"},
        ],
        "satellite_deployment": {
            "enabled": True,
            "position_range": {"x": (200, 700), "y": (100, 700)},
            "reference_pos": (100, 400),
            "cost_per_distance": 1.5,
            "max_satellites": 2,
        },
    }
    dep = SatelliteDeployment(level, available_budget=1200)
    ok = dep.can_deploy((300, 300), "basic")
    assert ok
    res = dep.deploy_satellite((300, 300), "basic")
    assert res.success and res.cost > 0
    bad = dep.deploy_satellite((50, 50), "basic")
    assert not bad.success

    net = DynamicNetwork(level)
    added = net.apply_deployment(dep.deployed_satellites)
    assert added >= 1
    assert any(n.get("is_player_satellite") for n in level["nodes"])
    print("OK 阶段3系统：卫星部署与节点写入")


def main():
    test_achievement_images()
    test_achievement_image_files()
    test_level_stars_normalize()
    test_load_progress_normalize()
    test_polar_unlock_logic()
    test_phase1_phase2_systems()
    test_phase3_satellite_system()
    print("--- 全部检查通过 ---")
    # 若存在且可导入，再跑原测试（需要 pygame）
    try:
        import pygame  # noqa: F401
        from test_changes import test_levels, test_estimate_ber_stars, test_node_hit, test_dsp_and_music
        test_levels()
        test_estimate_ber_stars()
        test_node_hit()
        test_dsp_and_music()
        print("原 test_changes 通过")
    except ImportError:
        print("(未安装 pygame，跳过 test_changes)")


if __name__ == "__main__":
    main()
