# -*- coding: utf-8 -*-
"""
成就系统 - 《大静默》阶段三 3.1
参照 成就.md 设计：进度/完美/技术/挑战/统计/隐藏 六类成就。
"""

from typing import Dict, Any, List, Set, Optional

# 成就分类
CATEGORY_PROGRESS = "progress"
CATEGORY_PERFECTION = "perfection"
CATEGORY_TECHNICAL = "technical"
CATEGORY_CHALLENGE = "challenge"
CATEGORY_STATISTICS = "statistics"
CATEGORY_HIDDEN = "hidden"


def _check_first_contact(stats: Dict[str, Any]) -> bool:
    return stats.get("levels_completed", 0) >= 1


def _check_getting_started(stats: Dict[str, Any]) -> bool:
    return stats.get("levels_completed", 0) >= 5


def _check_halfway_there(stats: Dict[str, Any]) -> bool:
    total = stats.get("total_levels", 10)
    return stats.get("levels_completed", 0) >= max(1, total // 2)


def _check_mission_complete(stats: Dict[str, Any]) -> bool:
    total = stats.get("total_levels", 10)
    return stats.get("levels_completed", 0) >= total


def _check_tech_unlocked(stats: Dict[str, Any]) -> bool:
    # 解锁 3 个新技术：默认已拥有 BPSK，因此需要 >=4
    return len(stats.get("unlocked_techs", [])) >= 4


def _check_full_arsenal(stats: Dict[str, Any]) -> bool:
    total = stats.get("total_techs", 8)
    return len(stats.get("unlocked_techs", [])) >= total


def _check_perfectionist(stats: Dict[str, Any]) -> bool:
    stars = stats.get("level_stars", {})
    return sum(1 for s in stars.values() if s >= 3) >= 3


def _check_triple_crown(stats: Dict[str, Any]) -> bool:
    return stats.get("consecutive_three_stars", 0) >= 5


def _check_flawless_victory(stats: Dict[str, Any]) -> bool:
    stars = stats.get("level_stars", {})
    total = stats.get("total_levels", 10)
    if len(stars) < total:
        return False
    return all(s >= 3 for s in stars.values())


def _check_ultra_low_ber(stats: Dict[str, Any]) -> bool:
    return stats.get("best_ber", 1.0) < 0.00001


def _check_speed_demon(stats: Dict[str, Any]) -> bool:
    return stats.get("fastest_time", 999) < 10


def _check_high_scorer(stats: Dict[str, Any]) -> bool:
    return stats.get("highest_score", 0) >= 200


def _check_bpsk_master(stats: Dict[str, Any]) -> bool:
    return stats.get("bpsk_clears", 0) >= 8


def _check_qpsk_expert(stats: Dict[str, Any]) -> bool:
    return stats.get("qpsk_clears", 0) >= 8


def _check_high_order_mod(stats: Dict[str, Any]) -> bool:
    return stats.get("8psk_clears", 0) >= 3


def _check_coding_theory(stats: Dict[str, Any]) -> bool:
    codes = ["none_clears", "repetition_clears", "hamming_clears", "polar_clears", "ldpc_clears"]
    return all(stats.get(c, 0) >= 3 for c in codes)


def _check_polar_pioneer(stats: Dict[str, Any]) -> bool:
    return stats.get("polar_clears", 0) >= 5


def _check_ldpc_legend(stats: Dict[str, Any]) -> bool:
    return stats.get("ldpc_hard_clears", 0) >= stats.get("total_hard_levels", 3)


def _check_minimalist(stats: Dict[str, Any]) -> bool:
    return stats.get("none_clears", 0) >= 5


def _check_no_repetition(stats: Dict[str, Any]) -> bool:
    return stats.get("no_repetition_full_clear", False)


def _check_low_snr_hero(stats: Dict[str, Any]) -> bool:
    return stats.get("low_snr_clears", 0) >= 3


def _check_one_shot(stats: Dict[str, Any]) -> bool:
    return stats.get("first_try_three_stars", 0) >= 5


def _check_comeback_king(stats: Dict[str, Any]) -> bool:
    return stats.get("comeback_achieved", False)


def _check_trial_and_error(stats: Dict[str, Any]) -> bool:
    return stats.get("max_configs_tried", 0) >= 15


def _check_veteran(stats: Dict[str, Any]) -> bool:
    return stats.get("total_playtime", 0) >= 18000


def _check_dedicated(stats: Dict[str, Any]) -> bool:
    return stats.get("total_playtime", 0) >= 36000


def _check_hundred_signals(stats: Dict[str, Any]) -> bool:
    return stats.get("total_transmissions", 0) >= 200


def _check_star_collector(stats: Dict[str, Any]) -> bool:
    return sum(stats.get("level_stars", {}).values()) >= 25


def _check_retry_master(stats: Dict[str, Any]) -> bool:
    return stats.get("total_retries", 0) >= 50


def _check_easter_egg(stats: Dict[str, Any]) -> bool:
    return stats.get("easter_egg_found", False)


def _check_shannon_tribute(stats: Dict[str, Any]) -> bool:
    return stats.get("shannon_limit_reached", False)


def _check_lucky_seven(stats: Dict[str, Any]) -> bool:
    return stats.get("hamming_clears", 0) >= 10


def _check_all_rounder(stats: Dict[str, Any]) -> bool:
    tried = len(stats.get("tried_combinations", set()))
    total = stats.get("total_combinations", 999)
    return tried >= total


def _check_perfect_streak(stats: Dict[str, Any]) -> bool:
    return stats.get("perfect_streak", 0) >= 10


def _check_tech_versatile(stats: Dict[str, Any]) -> bool:
    return all(stats.get(k, 0) >= 5 for k in ("bpsk_clears", "qpsk_clears", "8psk_clears"))


def _check_hard_mode_clear(stats: Dict[str, Any]) -> bool:
    return stats.get("hard_mode_completed", 0) >= stats.get("total_hard_levels", 3)


def _check_speed_runner(stats: Dict[str, Any]) -> bool:
    return stats.get("total_clear_time", 999999) < 1800


def _check_transmission_expert(stats: Dict[str, Any]) -> bool:
    return stats.get("total_transmissions", 0) >= 500


def _check_perfectionist_plus(stats: Dict[str, Any]) -> bool:
    total_levels = stats.get("total_levels", 10)
    return all(stats.get(f"level_{i}_score", 0) >= 200 for i in range(1, total_levels + 1))


# 成就定义表：id -> { name, desc, icon, category, hidden, check }
ACHIEVEMENTS: Dict[str, Dict[str, Any]] = {
    "first_contact": {
        "name": "第一次接触",
        "desc": "完成第一关",
        "icon": "🛰️",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_first_contact,
    },
    "getting_started": {
        "name": "初窥门径",
        "desc": "完成前5关",
        "icon": "📡",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_getting_started,
    },
    "halfway_there": {
        "name": "渐入佳境",
        "desc": "完成一半关卡",
        "icon": "🌐",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_halfway_there,
    },
    "mission_complete": {
        "name": "任务完成",
        "desc": "完成所有关卡",
        "icon": "🎯",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_mission_complete,
    },
    "tech_unlocked": {
        "name": "技术解锁",
        "desc": "解锁3个新技术",
        "icon": "🔓",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_tech_unlocked,
    },
    "full_arsenal": {
        "name": "武器库满载",
        "desc": "解锁所有技术",
        "icon": "🛠️",
        "category": CATEGORY_PROGRESS,
        "hidden": False,
        "check": _check_full_arsenal,
    },
    "perfectionist": {
        "name": "完美主义者",
        "desc": "获得3个三星关卡",
        "icon": "⭐",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_perfectionist,
    },
    "triple_crown": {
        "name": "三冠王",
        "desc": "连续5关获得三星",
        "icon": "👑",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_triple_crown,
    },
    "flawless_victory": {
        "name": "完美胜利",
        "desc": "所有关卡获得三星",
        "icon": "💎",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_flawless_victory,
    },
    "ultra_low_ber": {
        "name": "超低误码",
        "desc": "达成BER < 0.00001",
        "icon": "📉",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_ultra_low_ber,
    },
    "speed_demon": {
        "name": "速度恶魔",
        "desc": "10秒内完成关卡",
        "icon": "⚡",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_speed_demon,
    },
    "high_scorer": {
        "name": "高分选手",
        "desc": "单关得分200分",
        "icon": "🏆",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_high_scorer,
    },
    "perfect_streak": {
        "name": "完美连胜",
        "desc": "连续10关首次通关",
        "icon": "🔥",
        "category": CATEGORY_PERFECTION,
        "hidden": False,
        "check": _check_perfect_streak,
    },
    "bpsk_master": {
        "name": "BPSK大师",
        "desc": "使用BPSK完成8关",
        "icon": "🎓",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_bpsk_master,
    },
    "qpsk_expert": {
        "name": "QPSK专家",
        "desc": "使用QPSK完成8关",
        "icon": "🔬",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_qpsk_expert,
    },
    "high_order_mod": {
        "name": "高阶调制",
        "desc": "使用8PSK完成3关",
        "icon": "📶",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_high_order_mod,
    },
    "coding_theory": {
        "name": "编码理论家",
        "desc": "使用所有编码各完成3关",
        "icon": "📚",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_coding_theory,
    },
    "polar_pioneer": {
        "name": "Polar先驱",
        "desc": "使用Polar码完成5关",
        "icon": "🧊",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_polar_pioneer,
    },
    "ldpc_legend": {
        "name": "LDPC传奇",
        "desc": "使用LDPC完成所有困难关卡",
        "icon": "🌟",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_ldpc_legend,
    },
    "tech_versatile": {
        "name": "技术全才",
        "desc": "每种调制至少完成5关",
        "icon": "🎨",
        "category": CATEGORY_TECHNICAL,
        "hidden": False,
        "check": _check_tech_versatile,
    },
    "minimalist": {
        "name": "极简主义",
        "desc": "不使用编码完成5关",
        "icon": "🎯",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_minimalist,
    },
    "no_repetition": {
        "name": "拒绝重复",
        "desc": "不使用Repetition完成所有关卡",
        "icon": "🚫",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_no_repetition,
    },
    "low_snr_hero": {
        "name": "低信噪比英雄",
        "desc": "在SNR<0dB下完成3关",
        "icon": "💪",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_low_snr_hero,
    },
    "one_shot": {
        "name": "一击必杀",
        "desc": "首次尝试即三星通关5关",
        "icon": "🎲",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_one_shot,
    },
    "comeback_king": {
        "name": "逆转之王",
        "desc": "失败10次后成功通关",
        "icon": "🔄",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_comeback_king,
    },
    "trial_and_error": {
        "name": "试错精神",
        "desc": "同一关卡尝试15种配置",
        "icon": "🧪",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_trial_and_error,
    },
    "hard_mode_clear": {
        "name": "困难模式征服者",
        "desc": "完成所有困难模式关卡",
        "icon": "💀",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_hard_mode_clear,
    },
    "speed_runner": {
        "name": "速通玩家",
        "desc": "30分钟内通关所有关卡",
        "icon": "🏃",
        "category": CATEGORY_CHALLENGE,
        "hidden": False,
        "check": _check_speed_runner,
    },
    "veteran": {
        "name": "老兵",
        "desc": "游戏时长达到5小时",
        "icon": "🎖️",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_veteran,
    },
    "dedicated": {
        "name": "专注玩家",
        "desc": "游戏时长达到10小时",
        "icon": "⏰",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_dedicated,
    },
    "hundred_signals": {
        "name": "百次传输",
        "desc": "发送200次信号",
        "icon": "📊",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_hundred_signals,
    },
    "star_collector": {
        "name": "星星收集者",
        "desc": "累计获得25颗星",
        "icon": "✨",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_star_collector,
    },
    "retry_master": {
        "name": "重试大师",
        "desc": "重玩关卡50次",
        "icon": "🔁",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_retry_master,
    },
    "transmission_expert": {
        "name": "传输专家",
        "desc": "发送500次信号",
        "icon": "📡",
        "category": CATEGORY_STATISTICS,
        "hidden": False,
        "check": _check_transmission_expert,
    },
    "easter_egg": {
        "name": "彩蛋发现者",
        "desc": "发现隐藏彩蛋",
        "icon": "🥚",
        "category": CATEGORY_HIDDEN,
        "hidden": True,
        "check": _check_easter_egg,
        "image": "隐藏成就/彩蛋发现者.png",
    },
    "shannon_tribute": {
        "name": "香农致敬",
        "desc": "达到理论极限",
        "icon": "📡",
        "category": CATEGORY_HIDDEN,
        "hidden": True,
        "check": _check_shannon_tribute,
        "image": "隐藏成就/香农致敬.png",
    },
    "lucky_seven": {
        "name": "幸运七",
        "desc": "使用Hamming(7,4)完成10关",
        "icon": "🍀",
        "category": CATEGORY_HIDDEN,
        "hidden": True,
        "check": _check_lucky_seven,
        "image": "隐藏成就/幸运七.png",
    },
    "all_rounder": {
        "name": "全能选手",
        "desc": "尝试所有技术组合",
        "icon": "🌈",
        "category": CATEGORY_HIDDEN,
        "hidden": True,
        "check": _check_all_rounder,
        "image": "隐藏成就/全能选手.png",
    },
    "perfectionist_plus": {
        "name": "完美主义者+",
        "desc": "所有关卡满分",
        "icon": "💯",
        "category": CATEGORY_HIDDEN,
        "hidden": True,
        "check": _check_perfectionist_plus,
        "image": "隐藏成就/完美主义者.png",
    },
}

# 分类显示名
CATEGORY_NAMES = {
    CATEGORY_PROGRESS: "进度",
    CATEGORY_PERFECTION: "完美",
    CATEGORY_TECHNICAL: "技术",
    CATEGORY_CHALLENGE: "挑战",
    CATEGORY_STATISTICS: "统计",
    CATEGORY_HIDDEN: "隐藏",
}


class AchievementManager:
    """成就管理器：检测、保存、加载、按分类查询。"""

    def __init__(self) -> None:
        self.unlocked: Set[str] = set()
        self.newly_unlocked: List[str] = []

    def check_achievements(self, game_stats: Dict[str, Any]) -> List[str]:
        """根据当前 game_stats 检测新解锁成就，返回本次新解锁的 id 列表。"""
        self.newly_unlocked = []
        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id not in self.unlocked:
                try:
                    if ach_data["check"](game_stats):
                        self.unlocked.add(ach_id)
                        self.newly_unlocked.append(ach_id)
                except (KeyError, TypeError):
                    continue
        return self.newly_unlocked

    def get_achievement(self, ach_id: str) -> Optional[Dict[str, Any]]:
        return ACHIEVEMENTS.get(ach_id)

    def get_progress(self) -> tuple:
        total = len(ACHIEVEMENTS)
        unlocked = len(self.unlocked)
        return unlocked, total

    def get_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        return {k: v for k, v in ACHIEVEMENTS.items() if v["category"] == category}

    def save(self) -> List[str]:
        """返回已解锁成就 id 列表，用于持久化。"""
        return list(self.unlocked)

    def load(self, data: Optional[List[str]]) -> None:
        """从存档加载已解锁成就。"""
        if data is not None and isinstance(data, list):
            self.unlocked = set(data)
        else:
            self.unlocked = set()
