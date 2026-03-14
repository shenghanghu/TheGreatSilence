# -*- coding: utf-8 -*-
"""
技能解锁树 - 《大静默》阶段三 3.3
将“相关知识”改为技能树可视化：调制链 BPSK→QPSK→8PSK，编码链 Repetition→Hamming→Polar→LDPC。
"""

import pygame
from typing import List, Dict, Any, Optional, Tuple

# 技能树节点：(显示名, 解锁条件描述, 关联的 knowledge item 用于详情)
# 根据 levels 中 tech_unlock_info / tutorial_slides 归纳
TECH_TREE_STRUCT = [
    # 调制链
    {
        "id": "mod",
        "title": "调制方式",
        "nodes": [
            {"key": "BPSK", "name": "BPSK", "unlock_at_level": 1, "detail_key": "BPSK"},
            {"key": "QPSK", "name": "QPSK", "unlock_at_level": 2, "detail_key": "QPSK"},
            {"key": "8PSK", "name": "8PSK", "unlock_at_level": 0, "detail_key": "8PSK"},  # 0 = 未在关卡中
        ],
    },
    # 编码链
    {
        "id": "code",
        "title": "信道编码",
        "nodes": [
            {"key": "None", "name": "无", "unlock_at_level": 1, "detail_key": "None"},
            {"key": "Repetition(3,1)", "name": "Repetition(3,1)", "unlock_at_level": 2, "detail_key": "Repetition"},
            {"key": "Hamming(7,4)", "name": "Hamming(7,4)", "unlock_at_level": 3, "detail_key": "Hamming"},
            {"key": "Polar", "name": "Polar", "unlock_at_level": 5, "detail_key": "Polar"},
            {"key": "LDPC", "name": "LDPC", "unlock_at_level": 0, "detail_key": "LDPC"},
        ],
    },
]


def get_unlocked_techs(level_mgr, current_level_idx: int) -> set:
    """根据当前关卡进度返回已解锁技术 key 集合。关卡中编码可能为 Polar(N,K)，技能树节点 key 为 Polar，需归一化。"""
    unlocked = set()
    for i in range(min(current_level_idx + 1, len(level_mgr.levels))):
        lv = level_mgr.levels[i]
        for m in lv.get("available_mods", []):
            unlocked.add(m)
        for c in lv.get("available_codes", ["None"]):
            unlocked.add(c)
            # 技能树节点 key 为 "Polar"，关卡里是 "Polar(256,128)" 等，需视为已解锁 Polar
            if c and c.startswith("Polar"):
                unlocked.add("Polar")
    return unlocked


def build_tree_items_with_details(level_mgr) -> Dict[str, Dict[str, Any]]:
    """从 level_mgr 扫描 tech_unlock_info 与 tutorial_slides，生成 key -> { title, text, image } 供详情页使用。"""
    detail_map = {}
    for lv in level_mgr.levels:
        if "tech_unlock_info" in lv:
            t = lv["tech_unlock_info"]
            title = t.get("title", "")
            if "QPSK" in title:
                detail_map["QPSK"] = {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
            elif "Hamming" in title or "汉明" in title:
                detail_map["Hamming"] = {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
            elif "中继" in title or "Relay" in title:
                detail_map["Relay"] = {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
            elif "Polar" in title or "极化" in title:
                detail_map["Polar"] = {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
            elif "Laser" in title or "激光" in title:
                detail_map["Laser"] = {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
            elif "BP Decoder" in title or "SCL" in title:
                detail_map["Polar"] = detail_map.get("Polar") or {"title": title, "text": t.get("intro", "") + "\n\n" + t.get("specs", ""), "image": t.get("image")}
        if "tutorial_slides" in lv:
            for s in lv["tutorial_slides"]:
                if "BPSK" in s.get("title", ""):
                    detail_map["BPSK"] = {"title": s["title"], "text": s.get("text", ""), "image": s.get("image")}
                if "SNR" in s.get("title", ""):
                    detail_map["SNR"] = {"title": s["title"], "text": s.get("text", ""), "image": s.get("image")}
                if "BER" in s.get("title", ""):
                    detail_map["BER"] = {"title": s["title"], "text": s.get("text", ""), "image": s.get("image")}
    return detail_map


def draw_tech_tree_screen(
    surface,
    level_mgr,
    current_level_idx: int,
    btn_back,
    font,
    header_font,
    label_font,
    accent_color=(0, 180, 255),
    bg_color=(10, 12, 16),
    text_color=(220, 220, 220),
    width: int = 1600,
    height: int = 900,
) -> List[Tuple[Any, Dict[str, Any]]]:
    """
    绘制技能树界面。返回 [(rect, node_data), ...] 供主循环点击检测。
    node_data 含 key, name, unlocked, detail_item（用于详情页）。
    """
    unlocked_set = get_unlocked_techs(level_mgr, current_level_idx)
    detail_map = build_tree_items_with_details(level_mgr)
    surface.fill(bg_color)
    rects = []
    # 标题
    title_surf = header_font.render("技能树 (Technology Tree)", True, accent_color)
    surface.blit(title_surf, (width // 2 - title_surf.get_width() // 2, 28))
    sub = label_font.render("点击已解锁节点查看详情", True, (150, 160, 170))
    surface.blit(sub, (width // 2 - sub.get_width() // 2, 68))
    # 两行：调制链、编码链
    node_w, node_h = 140, 52
    gap = 48
    start_y_mod = 130
    start_y_code = 340
    for branch in TECH_TREE_STRUCT:
        nodes = branch["nodes"]
        start_y = start_y_mod if branch["id"] == "mod" else start_y_code
        total_w = len(nodes) * node_w + (len(nodes) - 1) * gap
        start_x = (width - total_w) // 2
        # 分支标题
        surf_title = font.render(branch["title"], True, (180, 200, 220))
        surface.blit(surf_title, (start_x, start_y - 32))
        for i, node in enumerate(nodes):
            x = start_x + i * (node_w + gap)
            y = start_y
            rect = pygame.Rect(x, y, node_w, node_h)
            key = node["key"]
            unlocked = key in unlocked_set
            # 颜色：已解锁绿，可解锁黄，未解锁灰
            if unlocked:
                color = (40, 100, 60)
                border = (80, 200, 120)
            else:
                color = (45, 45, 50)
                border = (70, 70, 80)
            s = pygame.Surface((node_w, node_h), pygame.SRCALPHA)
            s.fill((*color, 255))
            surface.blit(s, rect)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)
            name = node["name"]
            if len(name) > 12:
                name = name[:10] + ".."
            txt = label_font.render(name, True, text_color if unlocked else (100, 100, 110))
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
            detail_item = detail_map.get(node.get("detail_key", ""))
            rects.append((rect, {"key": key, "name": node["name"], "unlocked": unlocked, "detail_item": detail_item}))
        # 连线（简单横线）
        if len(nodes) > 1:
            line_y = start_y + node_h // 2
            for i in range(len(nodes) - 1):
                x1 = start_x + i * (node_w + gap) + node_w
                x2 = start_x + (i + 1) * (node_w + gap)
                pygame.draw.line(surface, (60, 70, 90), (x1, line_y), (x2, line_y), 2)
    btn_back.draw(surface)
    return rects
