import pygame
import sys
import math
import random
import numpy as np
import os # 新增
from dsp_engine import DSPEngine as dsp
from levels import LevelManager
from achievements import AchievementManager, ACHIEVEMENTS, CATEGORY_NAMES
from tech_tree import draw_tech_tree_screen
from budget_system import BudgetManager, calculate_level_reward, calculate_transmission_cost
from weather_system import WeatherSystem
from protocol_system import ProtocolSystem
from tech_balance import recommend_tech_combo
from transmission_control import PowerSlider, SegmentedTransmission
from satellite_system import SatelliteDeployment, DynamicNetwork, SATELLITE_TYPES
from causal_chain_animation import CausalChainAnimation

# --- 初始化 ---
pygame.init()
pygame.mixer.init() # 初始化音频混合器
WINDOW_WIDTH = 1600 # 拉宽，原为 1440
WINDOW_HEIGHT = 900 # 拉高，原为 800
HUD_WIDTH = 450 # 稍微增加 HUD 宽度，原为 420
MAP_WIDTH = WINDOW_WIDTH - HUD_WIDTH

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("The Great Silence - 大静默")
clock = pygame.time.Clock()

# --- 颜色定义 ---
BG_COLOR = (10, 12, 16)
PANEL_COLOR = (20, 24, 30)
MAP_BG_COLOR = (15, 18, 22)
ACCENT_COLOR = (0, 180, 255)
SUCCESS_COLOR = (50, 200, 100)
ERROR_COLOR = (230, 80, 80)
TEXT_COLOR = (220, 220, 220)

# --- 字体设置 ---
def get_font_name():
    # Attempt to load system font path directly
    preferred_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
    for f in preferred_fonts:
        try:
            if pygame.font.match_font(f):
                return f
        except:
            continue
    return None 

# Initialize font module before calling SysFont
pygame.font.init()
FONT_NAME = get_font_name()

def get_resource_path(relative_path):
    """获取资源绝对路径，兼容 PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_safe_font(font_name, size):
    """尝试加载中文字体，优先使用本地文件，否则尝试系统字体"""
    # 1. 优先尝试本地下载的字体 (wqy-microhei.ttc)
    local_font_path = get_resource_path(os.path.join("fonts", "wqy-microhei.ttc"))
    if os.path.exists(local_font_path):
        try:
            return pygame.font.Font(local_font_path, int(size))
        except Exception:
            pass
            
    # 2. 尝试备用本地字体 (兼容旧版或其他字体)
    local_font_path_alt = get_resource_path(os.path.join("fonts", "SourceHanSansCN-Regular.otf"))
    if os.path.exists(local_font_path_alt):
        try:
            return pygame.font.Font(local_font_path_alt, int(size))
        except Exception:
            pass

    # 3. 尝试系统字体
    try:
        if font_name is not None:
            return pygame.font.SysFont(font_name, size)
    except Exception:
        pass
    
    # 4. 最后的保底：使用 Pygame 默认内置字体
    return pygame.font.Font(None, int(size * 1.2))

# 使用安全加载函数
font = load_safe_font(FONT_NAME, 20)
header_font = load_safe_font(FONT_NAME, 32)
label_font = load_safe_font(FONT_NAME, 16)

STATE_START_SCREEN = 0
STATE_PLAYING = 1
STATE_BRIEFING = 2
STATE_TECH_UNLOCK = 3
STATE_EDU_SHOWCASE = 4
STATE_KNOWLEDGE_MENU = 5
STATE_KNOWLEDGE_DETAIL = 6 
STATE_CREDITS = 7  # 新增通关版权状态
STATE_CONCLUSION = 8 # 新增结论状态
STATE_SETTINGS = 9 # 新增设置状态
STATE_LETTER_VIEW = 10 # 新增信件展示状态
STATE_INTRO_1 = 11 # 新增开场 1: HOPE IS A WAVEFORM
STATE_INTRO_2 = 12 # 新增开场 2: IS ANYONE OUT THERE?
STATE_LEVEL_CATALOG = 13 # 关卡目录（选择关卡）
STATE_ACHIEVEMENTS = 14 # 成就界面（阶段三 3.1）
STATE_SATELLITE_DEPLOYMENT = 15 # 阶段三：卫星部署界面

# --- 存档路径 ---
SAVE_FILE = "save.json"

def _default_game_stats():
    """成就系统所需的默认游戏统计结构（成就.md 3.3）"""
    base = {
        "levels_completed": 0,
        "total_levels": 11,
        "level_stars": {},
        "unlocked_techs": ["BPSK"],
        "total_techs": 8,
        "best_ber": 1.0,
        "fastest_time": 999,
        "highest_score": 0,
        "consecutive_three_stars": 0,
        "perfect_streak": 0,
        "bpsk_clears": 0,
        "qpsk_clears": 0,
        "8psk_clears": 0,
        "none_clears": 0,
        "repetition_clears": 0,
        "hamming_clears": 0,
        "polar_clears": 0,
        "ldpc_clears": 0,
        "no_repetition_full_clear": False,
        "low_snr_clears": 0,
        "first_try_three_stars": 0,
        "comeback_achieved": False,
        "max_configs_tried": 0,
        "ldpc_hard_clears": 0,
        "total_hard_levels": 3,
        "hard_mode_completed": 0,
        "total_clear_time": 0,
        "total_playtime": 0,
        "total_transmissions": 0,
        "total_retries": 0,
        "easter_egg_found": False,
        "shannon_limit_reached": False,
        "tried_combinations": [],
        "total_combinations": 40,
        "level_fail_count": {},
        "level_first_try": {},  # {level_id(str): bool} 仅当“第一次挑战且未失败”才为 True
    }
    # 关卡分数记录（成就.md：perfectionist_plus 使用 level_{i}_score）
    for i in range(1, 12):
        base[f"level_{i}_score"] = 0
    return base

# 全局成就与统计（在 main() 中加载后使用）
g_game_stats = _default_game_stats()
g_achievement_manager = AchievementManager()
g_achievement_popup_queue = []  # 待显示的成就 id 列表（成就.md 4.3 小型通知依次显示）
g_achievement_notif_state = None  # 当前通知动画状态: {"ach_id", "phase", "start_ticks", "x_offset"}
g_achievement_scroll_y = 0  # 成就列表界面垂直滚动偏移（像素）
g_achievement_image_cache = {}  # {rel_path: Surface} 隐藏成就图片缓存
g_level_start_time = 0  # 进入关卡时的 ticks，用于计算用时

# 成就小型通知参数（成就.md 4.3：右上角、滑入 2s 停留 滑出、不阻塞）
NOTIF_W, NOTIF_H = 280, 80
NOTIF_SLIDE_MS, NOTIF_HOLD_MS = 220, 2000

def save_progress(level_idx, stars_dict, game_stats=None, achievements_list=None):
    """将关卡进度、星级、游戏统计与成就写入存档（阶段三 3.1）"""
    try:
        import json
        path = resource_path(SAVE_FILE)
        data = {
            "current_level_idx": level_idx,
            "level_stars": stars_dict,
        }
        if game_stats is not None:
            s = dict(game_stats)
            if "tried_combinations" in s and hasattr(s["tried_combinations"], "__iter__") and not isinstance(s["tried_combinations"], list):
                s["tried_combinations"] = list(s["tried_combinations"])
            data["game_stats"] = s
        if achievements_list is not None:
            data["achievements"] = achievements_list
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
    except Exception as e:
        print(f"Save failed: {e}")

def load_progress():
    """从存档读取进度、星级、游戏统计与成就；返回 (level_idx, stars_dict, game_stats, achievements_list) 或 None"""
    try:
        import json
        path = resource_path(SAVE_FILE)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        level_idx = data.get("current_level_idx", 0)
        raw_stars = data.get("level_stars", {})
        # 存档中 key 可能为字符串 "1","2"，关卡 id 为 int，统一为 int 避免选关时星星不显示
        stars_dict = {}
        for k, v in (raw_stars or {}).items():
            try:
                key = int(k) if isinstance(k, str) and k.isdigit() else k
                if isinstance(key, int):
                    stars_dict[key] = v
            except (ValueError, TypeError):
                pass
        game_stats = data.get("game_stats")
        achievements_list = data.get("achievements")
        return (level_idx, stars_dict, game_stats, achievements_list)
    except Exception as e:
        print(f"Load failed: {e}")
        return None


def build_stats_for_achievements(level_mgr, level_stars, levels_completed, game_stats):
    """构建成就检测用的完整 stats 字典（成就.md 3.3）。"""
    total_levels = len([l for l in level_mgr.levels if isinstance(l.get("id"), int)])
    unlocked_techs = []
    for i in range(min(levels_completed + 1, len(level_mgr.levels))):
        lv = level_mgr.levels[i]
        unlocked_techs.extend(lv.get("available_mods", []))
        unlocked_techs.extend(lv.get("available_codes", ["None"]))
    unlocked_techs = list(dict.fromkeys(unlocked_techs))
    all_techs = set()
    for lv in level_mgr.levels:
        if isinstance(lv.get("id"), int):
            all_techs.update(lv.get("available_mods", []))
            all_techs.update(lv.get("available_codes", ["None"]))
    total_techs = len(all_techs) if all_techs else 8
    # 连续三星：计算“最大连续三星段”（用于 triple_crown）
    stars_list = [level_stars.get(i, 0) for i in range(1, total_levels + 1)]
    consecutive = 0
    max_consecutive = 0
    for s in stars_list:
        if s >= 3:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    # 首次通关连胜：计算“最大连续首次通关段”（用于 perfect_streak）
    first_try_map = game_stats.get("level_first_try", {}) or {}
    streak = 0
    max_streak = 0
    for i in range(1, total_levels + 1):
        key = str(i)
        if first_try_map.get(key, False):
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return {
        "levels_completed": levels_completed,
        "total_levels": total_levels,
        "level_stars": level_stars,
        "unlocked_techs": unlocked_techs,
        "total_techs": total_techs,
        "best_ber": game_stats.get("best_ber", 1.0),
        "fastest_time": game_stats.get("fastest_time", 999),
        "highest_score": game_stats.get("highest_score", 0),
        "consecutive_three_stars": max(max_consecutive, game_stats.get("consecutive_three_stars", 0)),
        "perfect_streak": max(max_streak, game_stats.get("perfect_streak", 0)),
        **{k: game_stats.get(k, 0) for k in (
            "bpsk_clears", "qpsk_clears", "8psk_clears", "none_clears", "repetition_clears",
            "hamming_clears", "polar_clears", "ldpc_clears", "max_configs_tried",
            "total_playtime", "total_transmissions", "total_retries", "low_snr_clears",
            "first_try_three_stars", "ldpc_hard_clears", "total_hard_levels",
            "hard_mode_completed", "total_clear_time"
        )},
        **{k: game_stats.get(k, False) for k in (
            "no_repetition_full_clear", "comeback_achieved",
            "easter_egg_found", "shannon_limit_reached"
        )},
        "tried_combinations": game_stats.get("tried_combinations", []),
        "total_combinations": game_stats.get("total_combinations", 40),
        **{f"level_{i}_score": game_stats.get(f"level_{i}_score", 0) for i in range(1, total_levels + 1)},
    }


def calculate_score(ber, target_ber, time_spent, tech_used, level_id):
    """关卡评分详情（阶段三 3.2）：基础分+BER奖励+速度奖励+技术奖励，返回 (总分, 明细, 评级)。"""
    score = 0
    breakdown = []
    if target_ber > 0 and ber < target_ber:
        score += 100
        breakdown.append(("任务完成", 100))
    ber_ratio = (ber / target_ber) if target_ber > 0 else 0
    if ber_ratio < 0.1:
        score += 50
        breakdown.append(("误码率优秀", 50))
    elif ber_ratio < 0.5:
        score += 30
        breakdown.append(("误码率良好", 30))
    elif ber_ratio < 0.8:
        score += 10
        breakdown.append(("误码率合格", 10))
    if time_spent < 15:
        score += 30
        breakdown.append(("快速完成", 30))
    elif time_spent < 30:
        score += 15
        breakdown.append(("较快完成", 15))
    # 技术选择奖励（简化：使用推荐技术即加分）
    score += 20
    breakdown.append(("技术选择", 20))
    total = min(200, score)
    if total >= 200:
        grade = "S"
    elif total >= 150:
        grade = "A"
    elif total >= 100:
        grade = "B"
    else:
        grade = "C"
    return total, breakdown, grade


def fmt_num(value):
    """Readable number formatting for HUD/brief panels."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{n:,}"

# --- 音乐管理 ---
current_bgm = None
def play_bgm(music_name):
    global current_bgm
    if current_bgm == music_name:
        return
    
    # 如果 music_name 为 None，停止播放
    if music_name is None:
        pygame.mixer.music.stop()
        current_bgm = None
        return
    
    # 使用 resource_path 确保在不同目录下运行时路径依然正确
    rel_path = f"music/{music_name}"
    path = resource_path(rel_path)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1, fade_ms=2000) # 循环播放，2秒淡入
        current_bgm = music_name
    except Exception as e:
        print(f"无法加载音乐 {path}: {e}")

def get_level_music(level_id):
    # 根据用户要求的逻辑映射音乐（共11关）
    if level_id in [1, 2, 3, 4]: return "ofeliasdream.mp3"
    if level_id in [5, 6]: return "deepblue.mp3"
    if level_id in [7, 8]: return "fatalechoes.mp3"
    if level_id == 9: return "newdawn.mp3"
    if level_id in [10, 11]: return "dawnofchange.mp3"
    return "ofeliasdream.mp3"

current_state = STATE_START_SCREEN
previous_state = STATE_START_SCREEN # Default
level_mgr = LevelManager()
g_tech_unlock_level = None
g_conclusion_level = None # 存储结论画面关卡信息
g_original_level = None # 用于存储进入隐藏关前的原始关卡数据
g_hidden_level_visited = False # 追踪是否已访问隐藏关
g_was_level_complete = False # 记录进入隐藏关前是否已完成当前关卡
g_letter_scroll_idx = 0 # 信件打字机效果索引
g_edu_slides = [] # Store current slides
g_edu_slide_idx = 0
g_knowledge_list = [] # Cached list of knowledge items
g_current_knowledge_item = None
g_intro_alpha = 0 # 介绍画面透明度
g_intro_timer = 0 # 介绍画面计时器
g_level_stars = {}  # 每关最佳星级 {level_id: 1|2|3} (阶段 2.2)
g_level_catalog_rects = []  # 关卡目录每项的可点击区域 [(rect, level_idx), ...]

# --- 绘图工具 ---
credits_scroll_y = WINDOW_HEIGHT
CREDITS_TEXT = [
    "THE GREAT SILENCE",
    "大静默",
    "",
    "--- 任务完成 ---",
    "全球通信骨干网已成功修复",
    "大静默时代正式终结",
    "",
    "--- 制作团队 ---",
    "制作人员: 胡圣航， 林天意， 高雍皓",
    "数字化视觉: Pygame Framework",
    "信号处理引擎: NumPy & DSP Engine",
    "",
    "--- 背景音乐 ---",
    "Ofelia's Dream",
    "Deep Blue",
    "Fatal Echoes",
    "New Dawn",
    "Dawn of Change",
    "",
    "--- Music Source: Bensound.com ---",
    "Artist: FoePound",
    "License code: 3JBSWMCTGE7VRABZ",
    "",
    "Artist: Benjamin Tissot",
    "License code: QKNESAYELWLZGLW4",
    "License code: GDYDTYEL5JY5DKP7",
    "License code: 8PG0HEZ5K3ZHKI55",
    "",
    "Artist: Roman Senyk",
    "License code: J4GDMPQCWKNIYXU9",
    "",
    "感谢所有在实验室并肩作战的工程师们",
    "",
    "点击任意位置返回主菜单"
]

def draw_credits_screen(surface):
    global credits_scroll_y
    surface.fill(BG_COLOR)
    
    # 绘制静态背景装饰
    for i in range(100):
        # 伪随机但固定的星星（简单处理）
        x = (i * 137) % WINDOW_WIDTH
        y = (i * 263) % WINDOW_HEIGHT
        pygame.draw.circle(surface, (40, 50, 60), (x, y), 1)
         
    curr_y = credits_scroll_y
    for line in CREDITS_TEXT:
        if not line:
            curr_y += 20
            continue
        if line.startswith("---"):
            color = ACCENT_COLOR
            f = header_font
        elif line == "SIGNAL FLOW PROTOCOL":
            color = SUCCESS_COLOR
            f = header_font
        else:
            color = TEXT_COLOR
            f = font
            
        txt = f.render(line, True, color)
        surface.blit(txt, (WINDOW_WIDTH // 2 - txt.get_width() // 2, curr_y))
        curr_y += 45
    
    credits_scroll_y -= 1 # 滚动
    if credits_scroll_y < -len(CREDITS_TEXT) * 45 - 100:
        credits_scroll_y = WINDOW_HEIGHT # 循环滚动

def draw_bezier_curve(surface, color, p0, p1, p2, segments=20, width=2):
    points = []
    for t in np.linspace(0, 1, segments):
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    pygame.draw.lines(surface, color, False, points, width)

def get_bezier_point(t, p0, p1, p2):
    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
    return (x, y)

def draw_map_connection(surface, p0, p1, p2, progress=0.0, active=False):
    draw_bezier_curve(surface, (40, 50, 60), p0, p1, p2, segments=40, width=2)
    if active:
        curr_pos = get_bezier_point(progress, p0, p1, p2)
        pygame.draw.circle(surface, ACCENT_COLOR, (int(curr_pos[0]), int(curr_pos[1])), 6)
        partial_points = []
        for t in np.linspace(0, progress, int(20 * progress) + 2):
            partial_points.append(get_bezier_point(t, p0, p1, p2))
        if len(partial_points) > 1:
            pygame.draw.lines(surface, ACCENT_COLOR, False, partial_points, 3)

def draw_node(surface, pos, name, is_dest=False):
    color = (255, 100, 100) if is_dest else (100, 255, 100)
    pygame.draw.circle(surface, color, pos, 6)
    text = font.render(name, True, (200, 200, 200))
    rect = text.get_rect(center=(pos[0], pos[1] + 20))
    pygame.draw.rect(surface, (0,0,0,150), rect.inflate(10,4), border_radius=3)
    surface.blit(text, rect)

def render_text_wrapped(surface, text, pos, max_width, font, color=(200, 200, 200), align='left', draw=True):
    """Renders text and wraps it to a certain width. Returns the final Y position."""
    lines = []
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue
            
        current_line = ""
        i = 0
        while i < len(paragraph):
            char = paragraph[i]
            if ord(char) > 0x2E80: 
                unit = char
                i += 1
            else:
                unit = ""
                while i < len(paragraph) and ord(paragraph[i]) <= 0x2E80:
                    unit += paragraph[i]
                    if paragraph[i] == ' ':
                        i += 1
                        break
                    i += 1
            
            test_line = current_line + unit
            w, _ = font.size(test_line)
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = unit
                
        if current_line:
            lines.append(current_line)
    
    x_start, y = pos
    line_h = font.get_linesize()
    for line in lines:
        if line and draw:
            line_surf = font.render(line.strip(), True, color)
            lw, lh = line_surf.get_size()
            draw_x = x_start - lw // 2 if align == 'center' else x_start
            surface.blit(line_surf, (draw_x, y))
        y += line_h
    return y # Return the next Y position

# 用于绘制星座图残影的 Surface
constellation_surface = None

# ---------------------------------------------------------
# 术语悬停提示 (阶段 1.2)
# ---------------------------------------------------------
TOOLTIPS = {
    "BPSK": "二进制相移键控\n速度慢但最稳定",
    "QPSK": "正交相移键控\n速度是BPSK的2倍",
    "SNR": "信噪比\n数值越高信号越清晰",
    "BER": "误码率\n数值越低传输越准确",
    "Repetition(3,1)": "重复码\n每个比特重复3次",
    "Hamming(7,4)": "汉明码\n可自动纠正1位错误",
    "None": "无编码\n直接传输，无冗余",
    "udp": "UDP：低延迟，可靠性较弱\n适合快速试探链路",
    "tcp": "TCP：可靠性更高但开销大\n适合稳态传输",
    "sctp": "SCTP：多流平衡策略\n速度与可靠性折中",
    "quic": "QUIC：现代高速协议\n高预算下可提升吞吐",
}
def estimate_ber(snr_db, modulation, coding):
    """预估当前配置下的理论误码率（用于参数预览）"""
    if snr_db <= -20:
        return 0.5
    snr_linear = 10 ** (snr_db / 10.0)
    # BPSK: BER ≈ 0.5*erfc(sqrt(snr_linear))
    # QPSK: 近似同量级
    try:
        theoretical_ber = 0.5 * math.erfc(math.sqrt(snr_linear))
    except (ValueError, OverflowError):
        theoretical_ber = 1e-6
    theoretical_ber = max(1e-7, min(0.5, theoretical_ber))
    if coding and coding != "None":
        if coding == "Repetition(3,1)":
            theoretical_ber *= 0.08
        elif coding == "Hamming(7,4)":
            theoretical_ber *= 0.2
        elif coding.startswith("Polar"):
            theoretical_ber *= 0.12
    return theoretical_ber


def compute_power_snr_boost(power_dbm):
    """Power-to-SNR boost with diminishing returns."""
    delta = max(0.0, float(power_dbm) - 30.0)
    if delta <= 0:
        return 0.0
    return 12.0 * math.log10(1.0 + delta)

def estimate_stars(estimated_ber, target_ber):
    """根据预估 BER 与目标 BER 返回建议星级 (1-5)"""
    if target_ber <= 0:
        return 5
    ratio = estimated_ber / target_ber
    if ratio < 0.5: return 5
    if ratio < 0.8: return 4
    if ratio < 1.0: return 3
    if ratio < 1.5: return 2
    return 1

def calculate_stars(ber, thresholds):
    """根据实际 BER 与关卡 star_thresholds 计算获得星级 (0-3)"""
    if not thresholds:
        return 1 if ber < 0.1 else 0
    one = thresholds.get('one_star', 0.01)
    two = thresholds.get('two_star', 0.005)
    three = thresholds.get('three_star', 0.001)
    if ber <= three: return 3
    if ber <= two: return 2
    if ber <= one: return 1
    return 0

def draw_tooltip(surface, text, mouse_pos, font_obj=None):
    if not text or not font_obj:
        return
    lines = text.strip().split("\n")
    line_h = font_obj.get_linesize()
    max_w = 0
    for line in lines:
        w, _ = font_obj.size(line)
        max_w = max(max_w, w)
    box_w = max_w + 24
    box_h = len(lines) * line_h + 16
    tx = mouse_pos[0] + 20
    ty = mouse_pos[1] + 20
    if tx + box_w > surface.get_width():
        tx = mouse_pos[0] - box_w - 10
    if ty + box_h > surface.get_height():
        ty = surface.get_height() - box_h - 10
    if ty < 0:
        ty = 10
    tooltip_rect = pygame.Rect(tx, ty, box_w, box_h)
    s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    s.fill((20, 22, 28, 240))
    pygame.draw.rect(s, (60, 70, 85), s.get_rect(), 1, border_radius=4)
    surface.blit(s, tooltip_rect)
    for i, line in enumerate(lines):
        surf = font_obj.render(line, True, (220, 220, 220))
        surface.blit(surf, (tx + 12, ty + 8 + i * line_h))

# ---------------------------------------------------------
# 新增：名词翻译函数 (Game Flavor Translation)
# ---------------------------------------------------------
def get_tech_label(raw_name):
    """
    (Reverted) 将硬核通信术语保持原样，不再进行游戏化翻译。
    """
    return raw_name

# ---------------------------------------------------------
# 新增：简易教程管理器 (Tutorial Manager)
# ---------------------------------------------------------
class TutorialManager:
    def __init__(self):
        self.active = False
        self.step = 0
        self.completed = False
        self.mask_surf = None
        
    def start(self):
        self.active = True
        self.step = 0
        self.completed = False
        
    def next(self):
        self.step += 1
        
    def draw(self, surface, target_rect, text):
        if not self.active or self.completed: return
        
        # 1. 创建全屏遮罩
        if self.mask_surf is None or self.mask_surf.get_size() != surface.get_size():
            self.mask_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            
        # 填充半透明黑
        self.mask_surf.fill((0, 0, 0, 0)) # 清空
        self.mask_surf.fill((10, 12, 16, 200)) # 80% 不透明度背景
        
        # 2. 挖孔 (高亮区域)
        highlight_rect = target_rect.inflate(10, 10)
        
        # 将遮罩应用到屏幕 - 简单方案：画四周的矩形
        w, h = surface.get_size()
        tx, ty, tw, th = highlight_rect
        
        # Ensure coordinates are within screen bounds
        tx = max(0, tx)
        ty = max(0, ty)
        tw = min(w - tx, tw)
        th = min(h - ty, th)
        
        # Top
        if ty > 0: pygame.draw.rect(surface, (10, 12, 16, 220), (0, 0, w, ty))
        # Bottom
        if ty+th < h: pygame.draw.rect(surface, (10, 12, 16, 220), (0, ty+th, w, h-(ty+th)))
        # Left
        if tx > 0: pygame.draw.rect(surface, (10, 12, 16, 220), (0, ty, tx, th))
        # Right
        if tx+tw < w: pygame.draw.rect(surface, (10, 12, 16, 220), (tx+tw, ty, w-(tx+tw), th))
        
        # 3. 绘制高亮边框和文字
        pygame.draw.rect(surface, (255, 200, 50), (tx, ty, tw, th), 2, border_radius=5)
        
        # 绘制指引文字
        text_y = ty - 40 if ty > 100 else ty + th + 20
        text_surf = header_font.render(text, True, (255, 255, 255))
        
        bx = tx + tw // 2
        bg_rect = text_surf.get_rect(center=(bx, text_y))
        bg_rect.inflate_ip(20, 10)
        
        # Ensure text is on screen
        if bg_rect.left < 0: bg_rect.left = 10
        if bg_rect.right > w: bg_rect.right = w - 10
        
        pygame.draw.rect(surface, (0, 100, 200), bg_rect, border_radius=5)
        surface.blit(text_surf, (bg_rect.centerx - text_surf.get_width()//2, bg_rect.centery - text_surf.get_height()//2))

# 全局教程实例
g_tutorial = TutorialManager()

def draw_constellation(surface, symbols, cx, cy, scale=60):
    global constellation_surface
    
    # 区域大小
    width, height = 260, 200
    
    # 初始化或重新创建 Surface (如果大小匹配不上)
    if constellation_surface is None:
        constellation_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # 初始全黑背景 (改为完全透明，让背景色通过，或者保持半透明黑)
        constellation_surface.fill((0, 0, 0, 0)) 

    # 1. 实现余辉残影 + 电子云效果:
    # 相比之前简单的 fade，这里我们用更强一点的 fade 来保证旧点不要留太久变成线条，
    # 而是形成一种"区域感"。
    fade_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    # Alpha 值决定了残影的长度。值越小，残影越长。
    # 为了电子云效果，我们需要比较长的残影，所以 Alpha 小一点 (清除得慢)
    fade_surface.fill((15, 18, 22, 20)) 
    constellation_surface.blit(fade_surface, (0, 0))

    # 在 Surface 内部的中心坐标
    scx, scy = width // 2, height // 2

    # 绘制坐标轴 (每一帧稍微重绘一下以保持清晰，或者只画一次)
    # 为了保持残影效果，坐标轴也应该在 fade 之后重绘
    pygame.draw.line(constellation_surface, (60, 70, 80), (scx - 100, scy), (scx + 100, scy), 1)
    pygame.draw.line(constellation_surface, (60, 70, 80), (scx, scy - 100), (scx, scy + 100), 1)
    
    max_dots = 400
    step = max(1, len(symbols) // max_dots)
    
    # 辉光纹理 (预计算，提升性能)
    # 这是一个中心亮、边缘淡的圆
    if not hasattr(draw_constellation, "glow_surf"):
        # 增大光晕半径，制造朦胧感
        glow_radius = 8
        draw_constellation.glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        
        # 外圈辉光 (低Alpha，青色/Cyan) -> 对应参考图的边缘色
        # 参考图风格: 核心白，边缘青
        pygame.draw.circle(draw_constellation.glow_surf, (0, 255, 255, 30), (glow_radius, glow_radius), glow_radius)
        pygame.draw.circle(draw_constellation.glow_surf, (0, 200, 255, 60), (glow_radius, glow_radius), glow_radius - 2)
        
        # 内圈核心 (高Alpha，白色)
        pygame.draw.circle(draw_constellation.glow_surf, (255, 255, 255, 200), (glow_radius, glow_radius), 3)
    
    for s in symbols[::step]:
        # 映射到 Surface 坐标系
        x = scx + np.real(s) * scale
        y = scy - np.imag(s) * scale
        
        # 简单的边界检查
        if 0 < x < width and 0 < y < height:
            # 2. 绘制带辉光的点
            # 使用 BLEND_ADD 模式可以让重叠的点变得更亮，模拟光的叠加
            # 稍微加一点随机抖动来模拟电子云的不确定性 (可选)
            constellation_surface.blit(draw_constellation.glow_surf, 
                                     (int(x) - 8, int(y) - 8), 
                                     special_flags=pygame.BLEND_ADD)

    # 最后将这个带有残影和辉光的 Surface 绘制到主屏幕上对应的位置
    # 目标位置的左上角
    dest_x = cx - scx
    dest_y = cy - scy
    
    # 画边框
    pygame.draw.rect(surface, (60, 70, 80), (dest_x-1, dest_y-1, width+2, height+2), 1)
    surface.blit(constellation_surface, (dest_x, dest_y))

# --- Button ---
class Button:
    def __init__(self, x, y, w, h, text, callback=None, color=(60, 60, 70), hover_color=(80, 80, 90)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        c = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(surface, c, self.rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1, border_radius=5)
        txt = font.render(self.text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 用 rect 直接判定点击，避免未经过 hover 时点击无反应（如信件界“发送信号”）
            if event.button == 1 and self.rect.collidepoint(event.pos) and self.callback:
                self.callback()

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = max(min_val, min(initial_val, max_val))
        self.dragging = False

    def draw(self, surface):
        # Draw track
        pygame.draw.rect(surface, (40, 50, 60), self.rect, border_radius=5)
        pygame.draw.rect(surface, (100, 120, 140), self.rect, 1, border_radius=5)
        
        # Calculate handle position
        pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + pct * (self.rect.width - 20)
        handle_rect = pygame.Rect(handle_x, self.rect.y, 20, self.rect.height)
        
        # Draw handle
        color = (0, 180, 255) if self.dragging else (150, 200, 220)
        pygame.draw.rect(surface, color, handle_rect, border_radius=4)

    def handle_event(self, event):
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])
                changed = True
        return changed

    def update_val(self, mouse_x):
        rel_x = mouse_x - self.rect.x - 10 # Offset for handle center
        pct = max(0, min(1, rel_x / (self.rect.width - 20)))
        self.val = self.min_val + pct * (self.max_val - self.min_val)


# --- Visual Effects Classes ---
class Starfield:
    def __init__(self, count=200):
        self.stars = []
        for _ in range(count):
            self.stars.append({
                'x': np.random.randint(0, MAP_WIDTH),
                'y': np.random.randint(80, WINDOW_HEIGHT),
                'speed': np.random.uniform(0.05, 0.3),
                'size': np.random.choice([1, 1, 1, 2]),
                'alpha': np.random.randint(100, 255)
            })
    
    def update(self):
        for s in self.stars:
            s['x'] -= s['speed']
            if s['x'] < 0:
                s['x'] = MAP_WIDTH
                s['y'] = np.random.randint(80, WINDOW_HEIGHT)
    
    def draw(self, surface):
        for s in self.stars:
            # Simple stars
            pygame.draw.circle(surface, (s['alpha'], s['alpha'], s['alpha']), (int(s['x']), int(s['y'])), s['size'])

class EarthBackground:
    def __init__(self):
        self.angle = 0
        
    def draw(self, surface, center_pos=(200, 800), radius=500):
        # 绘制地球的大气层光晕（外发光）
        # 通过绘制多个同心圆，透明度递减来模拟
        for i in range(20):
            alpha = int(30 * (1 - i/20.0))
            if alpha <= 0: continue
            pygame.draw.circle(surface, (0, 100, 200, alpha), center_pos, radius + i*2, 2)
            
        # 绘制地球本体边缘（简单的反锯齿圆弧效果不够好，直接画大圆）
        # 这是一个巨大的暗色圆球
        pygame.draw.circle(surface, (5, 8, 12), center_pos, radius)
        pygame.draw.circle(surface, (20, 40, 60), center_pos, radius, 2)
        
        # 经纬线装饰 (简单的视觉效果)
        # 用椭圆模拟经线
        clip_rect = pygame.Rect(center_pos[0]-radius, center_pos[1]-radius, radius*2, radius*2)
        surface.set_clip(clip_rect) # 限制绘制区域在地球圆内
        
        for i in range(0, radius, 80):
             target_rect = pygame.Rect(center_pos[0] - i, center_pos[1] - radius, i*2, radius*2)
             pygame.draw.ellipse(surface, (30, 50, 70), target_rect, 1)
        
        # 恢复剪裁
        surface.set_clip(None)

class RadarPing:
    def __init__(self):
        self.pings = [] # list of [x, y, radius, alpha]
    
    def add(self, x, y):
        # 偶尔添加一个新的波纹
        if np.random.random() < 0.02: 
            self.pings.append([x, y, 0, 255])
            
    def update(self):
        for p in self.pings:
            p[2] += 1.5 # 半径增加
            p[3] -= 3   # 透明度减少
        self.pings = [p for p in self.pings if p[3] > 0]
        
    def draw(self, surface):
        for p in self.pings:
            # 绘制扩散的波纹圆环
            # 颜色采用青色/雷达色
            color = (0, 200, 255, int(p[3]))
            # 必须画在一个支持 alpha 的 surface 上或者直接用 circle (Pygame circle 不支持 alpha fill, 但支持 alpha line 如果 surface 是 alpha 的)
            # 这里为了简单，如果主 surface 不支持 alpha，效果可能打折，但主循环一般是 RGB。
            # 更好的做法是画到一个临时层
            target_surf = pygame.Surface((int(p[2]*2 + 4), int(p[2]*2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(target_surf, color, (int(p[2]+2), int(p[2]+2)), int(p[2]), 1)
            surface.blit(target_surf, (p[0] - p[2] - 2, p[1] - p[2] - 2), special_flags=pygame.BLEND_ADD)

class DynamicGrid:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.time = 0
        
    def update(self):
        self.time += 0.02
        # Simulate slow drift
        self.offset_x = (self.offset_x + 0.1) % 50
        
    def draw(self, surface):
        # Draw vertical lines
        for x in range(0, MAP_WIDTH + 50, 50):
            draw_x = x - self.offset_x
            
            # Simple line for now
            alpha = 20 + 5 * np.sin(draw_x*0.01 + self.time)
            color = (25, 30 + int(alpha), 40 + int(alpha))
            
            start_pos = (draw_x, 80)
            end_pos = (draw_x, WINDOW_HEIGHT)
            pygame.draw.line(surface, color, start_pos, end_pos, 1)

        # Draw horizontal lines
        for y in range(80, WINDOW_HEIGHT, 50):
            # Breathing effect on color
            alpha = 30 + 10 * np.sin(y*0.02 + self.time)
            color = (25, int(alpha), 40)
            pygame.draw.line(surface, color, (0, y), (MAP_WIDTH, y), 1)

def generate_asteroid_polygon(radius):
    num_points = np.random.randint(5, 9)
    points = []
    for i in range(num_points):
        angle = (2 * np.pi / num_points) * i
        r = radius * (0.7 + 0.3 * np.random.rand()) # Variance in radius
        points.append((r * np.cos(angle), r * np.sin(angle)))
    return points

# Global VFX instances
vfx_stars = Starfield()

vfx_earth = EarthBackground()
vfx_radar = RadarPing()
vfx_grid = DynamicGrid()

import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def draw_image_fit(surface, img_path, center_pos, max_size):
    
    # Use resource_path to find the file
    full_path = resource_path(img_path)
    
    if not os.path.exists(full_path): 
        # print(f"Image not found: {full_path}")
        return

    try:
        img = pygame.image.load(full_path).convert_alpha()
        # Scale to fit max_size (w, h) keeping aspect ratio
        iw, ih = img.get_size()
        mw, mh = max_size
        scale = min(mw/iw, mh/ih)
        if scale < 1.0 or scale > 1.0: # Always scale to fit box nicely
             new_size = (int(iw*scale), int(ih*scale))
             img = pygame.transform.smoothscale(img, new_size)
        rect = img.get_rect(center=center_pos)
        surface.blit(img, rect)
    except Exception as e:
        print(f"Failed to load image {img_path}: {e}")


def load_achievement_image(rel_path, max_w, max_h):
    """加载成就图片并缩放到 (max_w, max_h) 内，带缓存。返回 Surface 或 None。"""
    global g_achievement_image_cache
    key = (rel_path, max_w, max_h)
    if key in g_achievement_image_cache:
        return g_achievement_image_cache[key]
    full_path = resource_path(rel_path)
    if not os.path.exists(full_path):
        return None
    try:
        img = pygame.image.load(full_path).convert_alpha()
        iw, ih = img.get_size()
        scale = min(max_w / iw, max_h / ih, 1.0)
        new_size = (int(iw * scale), int(ih * scale))
        if new_size[0] < 1 or new_size[1] < 1:
            return None
        img = pygame.transform.smoothscale(img, new_size)
        g_achievement_image_cache[key] = img
        return img
    except Exception:
        return None

# 开始页背景：蓝色星星划过特效（持久化列表，每帧更新）
_g_start_stars = []

def _init_start_stars():
    global _g_start_stars
    if _g_start_stars:
        return
    for _ in range(48):
        _g_start_stars.append({
            'x': np.random.randint(0, WINDOW_WIDTH),
            'y': np.random.randint(0, WINDOW_HEIGHT),
            'speed': 0.8 + np.random.rand() * 1.5,
            'size': 1 + int(np.random.rand() * 2),
            'bright': 0.4 + np.random.rand() * 0.6,
        })

def _update_draw_start_stars(surface):
    _init_start_stars()
    for s in _g_start_stars:
        s['x'] -= s['speed']
        if s['x'] < -4:
            s['x'] = WINDOW_WIDTH + 4
            s['y'] = np.random.randint(0, WINDOW_HEIGHT)
        r = int(80 * s['bright'])
        g = int(160 * s['bright'])
        b = int(255 * s['bright'])
        color = (r, g, b)
        pygame.draw.circle(surface, color, (int(s['x']), int(s['y'])), s['size'])

def draw_start_screen(surface, btn_new_game, btn_continue, btn_level_catalog, btn_kv, btn_settings, btn_achievements=None):
    surface.fill(BG_COLOR)
    _update_draw_start_stars(surface)
    
    # Title
    t1 = header_font.render("THE GREAT SILENCE", True, ACCENT_COLOR)
    t2 = header_font.render("大静默", True, (255, 255, 255))
    mx = WINDOW_WIDTH // 2
    surface.blit(t1, (mx - t1.get_width() // 2, 200))
    surface.blit(t2, (mx - t2.get_width() // 2, 248))
    
    # 分隔线与说明：全竖排下留足间距
    line_y = 318
    pygame.draw.line(surface, (50, 60, 70), (mx - 200, line_y), (mx + 200, line_y), 1)
    hint = label_font.render("新游戏覆盖存档 · 继续游戏读取本地存档", True, (120, 130, 140))
    surface.blit(hint, (mx - hint.get_width() // 2, line_y + 14))

    btn_new_game.draw(surface)
    btn_continue.draw(surface)
    btn_level_catalog.draw(surface)
    btn_kv.draw(surface)
    btn_settings.draw(surface)
    # 阶段三 3.1：成就入口放在左下角
    if btn_achievements:
        btn_achievements.draw(surface)

def draw_intro_screen(surface, text, color, alpha):
    surface.fill((0, 0, 0)) # 纯黑背景
    
    # 字体加载逻辑有点特殊，因为 alpha 需要 Surface 变换
    # 使用大一点的字体
    # 注意：为了性能，这里最好不要每帧重新加载 Font，为了简单我们直接用全局 header_font 如果够大的话
    # 这里我们还是临时创建一个大号字体
    try:
        f = pygame.font.Font(None, 60) # 使用默认字体，大号
    except:
        f = header_font
        
    # Render text to a temporary surface
    txt_surf = f.render(text, True, color)
    
    # Create an alpha-compatible surface
    alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
    
    # Blit text onto alpha surf
    alpha_surf.blit(txt_surf, (0, 0))
    
    # Apply alpha
    alpha_surf.set_alpha(alpha)
    
    # Center
    cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    surface.blit(alpha_surf, (cx - alpha_surf.get_width() // 2, cy - alpha_surf.get_height() // 2))

def draw_settings_screen(surface, btn_back, slider_vol):
    surface.fill(BG_COLOR)
    
    # Title
    t_surf = header_font.render("设置", True, ACCENT_COLOR)
    surface.blit(t_surf, (WINDOW_WIDTH // 2 - t_surf.get_width() // 2, 100))
    
    # Volume Control Area
    label_vol = font.render(f"音乐音量: {int(slider_vol.val * 100)}%", True, TEXT_COLOR)
    surface.blit(label_vol, (WINDOW_WIDTH // 2 - 150, 300))
    
    slider_vol.rect.centerx = WINDOW_WIDTH // 2
    slider_vol.rect.y = 350
    slider_vol.draw(surface)
    
    # Back button
    btn_back.draw(surface)

def _draw_lock_icon(surface, center_x, center_y, size=14, color=(120, 120, 130)):
    """在给定中心绘制简易锁图标（矩形+顶部弧线），表示未解锁"""
    r = size // 2
    body = pygame.Rect(center_x - r, center_y - r // 2, r * 2, r + 2)
    pygame.draw.rect(surface, color, body, border_radius=2)
    # 锁扣弧线
    arc_rect = pygame.Rect(center_x - r - 2, center_y - r - 4, r * 2 + 4, r + 2)
    pygame.draw.arc(surface, color, arc_rect, np.pi, 0, 2)

def draw_level_catalog(surface, level_mgr, stars_dict, btn_back):
    """绘制关卡目录，并填充 g_level_catalog_rects 供点击检测；未解锁关卡显示锁且不可点击"""
    global g_level_catalog_rects
    surface.fill(BG_COLOR)
    title = header_font.render("关卡目录", True, ACCENT_COLOR)
    surface.blit(title, (80, 25))
    sub = label_font.render("点击已解锁关卡进入简报 · 进度已自动保存", True, (150, 150, 150))
    surface.blit(sub, (80, 58))
    pygame.draw.line(surface, ACCENT_COLOR, (80, 85), (WINDOW_WIDTH - 80, 85), 2)
    g_level_catalog_rects = []
    y = 115
    col_w = 380
    gap = 24
    for idx, lv in enumerate(level_mgr.levels):
        lid = lv.get("id")
        if isinstance(lid, str):
            continue
        row = (idx // 3)
        col = idx % 3
        x = 80 + col * (col_w + gap)
        cy = y + row * 72
        rect = pygame.Rect(x, cy, col_w, 64)
        unlocked = idx <= level_mgr.current_level_idx
        if unlocked:
            g_level_catalog_rects.append((rect, idx))
        color = (28, 35, 45)
        if not unlocked:
            color = (22, 26, 32)
        if idx == level_mgr.current_level_idx:
            pygame.draw.rect(surface, (40, 55, 75), rect, border_radius=8)
            pygame.draw.rect(surface, ACCENT_COLOR, rect, 2, border_radius=8)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, (50, 60, 75), rect, 1, border_radius=8)
        title_text = lv.get("title", f"关卡 {lid}")
        star_count = stars_dict.get(lid, 0)
        star_str = "★" * star_count + "☆" * (3 - star_count)
        text_color = (220, 220, 220) if unlocked else (100, 100, 110)
        surf_title = label_font.render(f"{lid}. {title_text}", True, text_color)
        surf_star = label_font.render(star_str, True, (255, 200, 50)) if unlocked else label_font.render("—", True, (80, 80, 90))
        surface.blit(surf_title, (x + 12, cy + 10))
        surface.blit(surf_star, (x + 12, cy + 36))
        if not unlocked:
            _draw_lock_icon(surface, x + col_w - 24, cy + 32, 16, (100, 100, 110))
    btn_back.draw(surface)

def draw_briefing_screen(surface, level, btn):
    surface.fill(BG_COLOR)
    if "pending_weather" not in level:
        level["pending_weather"] = random.choice(["clear", "cloudy", "rain", "storm", "solar_flare"])
    
    # Title
    phase = font.render(level['phase'], True, ACCENT_COLOR)
    title = header_font.render(level['title'], True, (255, 255, 255))
    surface.blit(phase, (100, 100))
    surface.blit(title, (100, 130))
    pygame.draw.line(surface, ACCENT_COLOR, (100, 170), (1100, 170), 2)
    
    # Story
    y = 200
    if 'story_intro' in level:
        y = render_text_wrapped(surface, level['story_intro'], (100, y), 1000, font, TEXT_COLOR)
            
    # Mission Info
    y += 40
    pygame.draw.rect(surface, (20, 24, 30), (100, y, 1000, 200), border_radius=10)
    pygame.draw.rect(surface, (60, 60, 70), (100, y, 1000, 200), 1, border_radius=10)
    
    y_inner = y + 20
    if 'mission_info' in level:
        # Separate lines that might have "目标" for coloring, or just wrap all
        for line in level['mission_info'].split('\n'):
            col = (255, 200, 50) if "目标" in line else TEXT_COLOR
            y_inner = render_text_wrapped(surface, line, (130, y_inner), 940, font, col)
            y_inner += 5 # padding
            
    # Weather & tech impact preview before mission start
    y_weather = y + 220
    weather_key = level.get("pending_weather", "clear")
    weather_probe = WeatherSystem()
    weather_probe.set_weather(weather_key)
    w_info = weather_probe.get_weather_info()
    pygame.draw.rect(surface, (18, 26, 36), (100, y_weather, 1000, 120), border_radius=10)
    pygame.draw.rect(surface, (70, 90, 120), (100, y_weather, 1000, 120), 1, border_radius=10)
    surface.blit(font.render(f"天气预报: {w_info.name} ({weather_key})", True, (180, 220, 255)), (120, y_weather + 14))
    effect_lines = [
        f"总体影响: {w_info.description}",
        f"SNR修正: {w_info.snr_penalty:+.1f} dB   激光附加: {w_info.laser_penalty:+.1f} dB   BER倍率: x{w_info.ber_multiplier:.2f}",
    ]
    available_mods = level.get("available_mods", [])
    available_codes = level.get("available_codes", [])
    if "BPSK" in available_mods and weather_key in ("storm", "solar_flare"):
        effect_lines.append("技术建议: BPSK 在当前天气更稳健。")
    if "QPSK" in available_mods and weather_key == "clear":
        effect_lines.append("技术建议: 晴朗环境可优先尝试 QPSK 提升吞吐。")
    if any((c or "").startswith("Polar") for c in available_codes):
        effect_lines.append("技术建议: Polar 码在干扰天气有额外抗扰收益。")
    y_w = y_weather + 44
    for line in effect_lines[:4]:
        y_w = render_text_wrapped(surface, line, (120, y_w), 960, label_font, TEXT_COLOR)
        y_w += 4

    # Reward
    y_reward = y_weather + 140
    if 'reward' in level:
        lbl = label_font.render("任务奖励:", True, SUCCESS_COLOR)
        val = font.render(level['reward'], True, (255, 255, 255))
        surface.blit(lbl, (100, y_reward))
        surface.blit(val, (100, y_reward + 25))
    # 已获星级 (阶段 2.2)
    lid = level.get('id')
    key = int(lid) if isinstance(lid, str) and (lid or "").isdigit() else lid
    earned = g_level_stars.get(key, 0)
    star_y = y_reward + 55
    surface.blit(label_font.render("已获星级:", True, (255, 200, 50)), (100, star_y))
    GOLD, GRAY = (255, 200, 50), (80, 80, 80)
    for i in range(3):
        x = 200 + i * 28
        if i < earned:
            star_surf = label_font.render("★", True, GOLD)
        else:
            star_surf = label_font.render("☆", True, GRAY)
        surface.blit(star_surf, (x, star_y))

    btn.draw(surface)


def draw_satellite_deployment_screen(
    surface,
    level,
    deployment,
    selected_sat_type,
    selected_pos,
    deploy_message,
    btn_confirm,
    btn_skip,
    btn_done,
):
    surface.fill(BG_COLOR)
    pygame.draw.rect(surface, (16, 22, 32), (0, 0, WINDOW_WIDTH, 100))
    surface.blit(header_font.render("卫星部署阶段", True, ACCENT_COLOR), (40, 24))
    surface.blit(font.render(f"关卡: {level.get('title', '')}", True, TEXT_COLOR), (40, 60))

    # Deploy area
    px1, px2 = deployment.position_range["x"]
    py1, py2 = deployment.position_range["y"]
    area_rect = pygame.Rect(px1, py1, px2 - px1, py2 - py1)
    pygame.draw.rect(surface, (20, 36, 52), area_rect)
    pygame.draw.rect(surface, (70, 120, 170), area_rect, 2)
    surface.blit(label_font.render("可部署区域（点击选点）", True, (180, 220, 255)), (area_rect.x + 10, area_rect.y + 10))

    # Existing nodes
    for node in level.get("nodes", []):
        color = (100, 255, 255) if node.get("type") == "src" else (255, 120, 120) if node.get("type") == "dest" else (220, 220, 120)
        pygame.draw.circle(surface, color, (int(node["pos"][0]), int(node["pos"][1])), 7)
        txt = label_font.render(node.get("name", ""), True, (210, 210, 210))
        surface.blit(txt, (int(node["pos"][0]) + 10, int(node["pos"][1]) - 10))

    # Reference point
    ref = deployment.reference_pos
    pygame.draw.circle(surface, (255, 210, 90), (int(ref[0]), int(ref[1])), 8)
    surface.blit(label_font.render("参考点", True, (255, 210, 90)), (int(ref[0]) + 10, int(ref[1]) - 18))

    # Deployed satellites
    for sat in deployment.deployed_satellites:
        pygame.draw.circle(surface, (120, 255, 140), (int(sat["pos"][0]), int(sat["pos"][1])), 9)
        surface.blit(label_font.render(sat["name"], True, (190, 255, 200)), (int(sat["pos"][0]) + 10, int(sat["pos"][1]) - 10))

    # Selected point preview
    preview_cost = 0
    if selected_pos is not None:
        pygame.draw.circle(surface, (0, 200, 255), (int(selected_pos[0]), int(selected_pos[1])), 9, 2)
        preview_cost = deployment.get_deploy_cost(selected_pos, selected_sat_type)
        pygame.draw.line(surface, (90, 120, 160), ref, selected_pos, 1)

    # Right panel
    panel_x = MAP_WIDTH + 10
    pygame.draw.rect(surface, (20, 24, 30), (MAP_WIDTH, 0, HUD_WIDTH, WINDOW_HEIGHT))
    pygame.draw.rect(surface, ACCENT_COLOR, (MAP_WIDTH, 0, HUD_WIDTH, WINDOW_HEIGHT), 2)
    surface.blit(font.render(f"预算: {fmt_num(deployment.budget)}/{fmt_num(deployment.initial_budget)}", True, (255, 215, 120)), (panel_x, 30))
    surface.blit(label_font.render(f"已部署: {len(deployment.deployed_satellites)} / {deployment.max_satellites}", True, (180, 210, 240)), (panel_x, 60))

    y = 290
    selected_sat = SATELLITE_TYPES.get(selected_sat_type, SATELLITE_TYPES["basic"])
    info_rect = pygame.Rect(panel_x, y, HUD_WIDTH - 24, 110)
    pygame.draw.rect(surface, (34, 40, 48), info_rect, border_radius=6)
    pygame.draw.rect(surface, (110, 130, 160), info_rect, 1, border_radius=6)
    surface.blit(label_font.render(f"当前类型: {selected_sat['name']} ({selected_sat_type})", True, (220, 235, 255)), (info_rect.x + 10, info_rect.y + 10))
    surface.blit(label_font.render(f"基础成本: {fmt_num(selected_sat['base_cost'])}  增益: {selected_sat['antenna_gain']}dBi", True, (180, 210, 235)), (info_rect.x + 10, info_rect.y + 36))
    surface.blit(label_font.render(f"说明: {selected_sat['description']}", True, (170, 190, 210)), (info_rect.x + 10, info_rect.y + 62))

    if selected_pos is not None:
        surface.blit(label_font.render(f"选中坐标: ({int(selected_pos[0])}, {int(selected_pos[1])})", True, (220, 220, 220)), (panel_x, y + 124))
        surface.blit(label_font.render(f"预估成本: {fmt_num(preview_cost)}", True, (255, 215, 120)), (panel_x, y + 148))

    if deploy_message:
        surface.blit(label_font.render(deploy_message, True, (255, 170, 170)), (40, WINDOW_HEIGHT - 40))

    btn_confirm.draw(surface)
    btn_skip.draw(surface)
    btn_done.draw(surface)

def draw_letter_view(surface, level, btn):
    surface.fill((10, 10, 12)) 

    # Background scanlines
    for i in range(0, WINDOW_HEIGHT, 4):
        pygame.draw.line(surface, (15, 20, 25), (0, i), (WINDOW_WIDTH, i), 1)

    # Header
    h_surf = header_font.render("加密传输协议", True, (0, 200, 100))
    surface.blit(h_surf, (100, 80))

    # Meta Info
    # 获取原始协议名用于显示
    raw_proto = level.get('available_mods', ['BPSK'])[0]
    display_proto = get_tech_label(raw_proto) # 使用翻译后的名字

    meta_lines = [
        f"发送源:   {level.get('nodes', [{}])[0].get('name', 'UNKNOWN')}",
        f"接收端:   {level.get('nodes', [{}])[-1].get('name', 'UNKNOWN')}",
        f"日期:     2053-11-0{level.get('id', 0)}",
        f"协议:     {display_proto}",
        "------------------------------------------------------------"
    ]
    
    y = 140
    for line in meta_lines:
        s = font.render(line, True, (100, 255, 200)) # Green terminal style
        surface.blit(s, (100, y))
        y += 30

    # Letter Body (Typewriter effect)
    y += 20
    message = level.get('message', "")
    
    # Show chars based on global scroll index
    # We want a cursor effect
    chars_show = min(len(message), int(g_letter_scroll_idx))
    text_to_show = message[:chars_show]
    
    # Render with wrapping
    final_y = render_text_wrapped(surface, text_to_show, (100, y), 1000, font, (220, 220, 220))
    
    # Cursor
    if chars_show < len(message):
        # Calculate approximate cursor position (difficult with wrapped text function)
        # Simplified: just draw a blinking block at end of last line or separate
        if int(pygame.time.get_ticks() / 500) % 2 == 0:
            pass # Blink
    else:
        # Finished typing
        # Draw "END OF MESSAGE"
        end_surf = label_font.render("[信息结束]", True, (80, 80, 80))
        surface.blit(end_surf, (100, final_y + 20))
        
        # Show Button
        btn.draw(surface)

def draw_edu_showcase_screen(surface, btn_next):
    surface.fill(BG_COLOR)
    
    slides = g_edu_slides if g_edu_slides else []
    if not slides:
        btn_next.draw(surface)
        return

    idx = max(0, min(g_edu_slide_idx, len(slides) - 1))
    slide = slides[idx]
    
    # Title
    t_surf = header_font.render(slide['title'], True, ACCENT_COLOR)
    surface.blit(t_surf, (WINDOW_WIDTH//2 - t_surf.get_width()//2, 50))
    
    # Image
    slide_img_rel = slide['image']
    full_img_path = resource_path(slide_img_rel)
    
    try:
        if os.path.exists(full_img_path):
            img = pygame.image.load(full_img_path)
            iw, ih = img.get_size()
            scale = min(800/iw, 500/ih)
            if scale < 1:
                img = pygame.transform.scale(img, (int(iw*scale), int(ih*scale)))
            
            ix = WINDOW_WIDTH//2 - img.get_width()//2
            iy = WINDOW_HEIGHT//2 - img.get_height()//2 - 50
            surface.blit(img, (ix, iy))
            pygame.draw.rect(surface, (100, 100, 100), (ix-2, iy-2, img.get_width()+4, img.get_height()+4), 2)
    except Exception as e:
        print(f"Failed to draw edu image {full_img_path}: {e}")
        
    # Text
    y_txt = 650
    if 'text' in slide:
        render_text_wrapped(surface, slide['text'], (WINDOW_WIDTH//2, y_txt), 1000, font, TEXT_COLOR, align='center')
        
    # Page indicator
    p_txt = label_font.render(f"Page {idx+1}/{len(slides)}", True, (150, 150, 150))
    surface.blit(p_txt, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 80))

    btn_next.text = "开始任务" if idx >= len(slides) - 1 else "下一页"
    btn_next.draw(surface)

def draw_analysis_report(surface, result, close_btn):
    if not result or 'analysis_data' not in result:
        return
        
    data = result['analysis_data']
    
    # 获取翻译名
    lbl_mod = get_tech_label(data['mod_type'])
    lbl_code = get_tech_label(data['code_type'])
    
    # 获取翻译名
    lbl_mod = get_tech_label(data['mod_type'])
    lbl_code = get_tech_label(data['code_type'])

    # 1. Background Dimmer
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 8, 15, 245)) # Darker, more solid
    surface.blit(overlay, (0, 0))
    
    # 2. Main Container
    cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    w, h = 1100, 700
    rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
    
    pygame.draw.rect(surface, (15, 20, 28), rect, border_radius=15)
    pygame.draw.rect(surface, (50, 150, 255), rect, 2, border_radius=15)
    
    # Header
    title = header_font.render("回声重构报告", True, (255, 255, 255))
    surface.blit(title, (rect.x + 40, rect.y + 30))
    pygame.draw.line(surface, (60, 70, 80), (rect.x + 40, rect.y + 80), (rect.x + w - 40, rect.y + 80), 1)

    # --- Helper: Bit Grid Drawing ---
    def draw_bit_grid(surf, pos, bits, label, color_on=(0, 255, 200), color_off=(40, 45, 55), highlight_errors=None):
        surf.blit(label_font.render(label, True, (150, 150, 150)), pos)
        x_st, y_st = pos[0] + 120, pos[1] - 4
        slot_w, slot_h = 16, 22
        gap = 4
        
        if bits is None: return
        
        # Draw up to 24 bits
        for i, b in enumerate(bits[:24]):
            bx = x_st + i * (slot_w + gap)
            # Add extra gap every 8 bits
            bx += (i // 8) * 10
            
            r = pygame.Rect(bx, y_st, slot_w, slot_h)
            
            # Error Highlighting
            is_error = False
            if highlight_errors is not None and i < len(highlight_errors):
                if highlight_errors[i]: is_error = True
            
            bg_col = color_off
            if is_error:
                bg_col = (80, 20, 20)
                pygame.draw.rect(surf, (255, 50, 50), r.inflate(4, 4), width=1, border_radius=3)
            
            pygame.draw.rect(surf, bg_col, r, border_radius=3)
            
            txt_col = color_on if b == 1 else (100, 105, 115)
            if is_error: txt_col = (255, 100, 100)
            
            bit_t = label_font.render(str(int(b)), True, txt_col)
            surf.blit(bit_t, (r.centerx - bit_t.get_width()//2, r.centery - bit_t.get_height()//2))

    # --- Helper: Waveform Drawing ---
    def draw_waveform(surf, inner_rect, bits, mod_type, noise_snr=None):
        pygame.draw.rect(surf, (5, 5, 8), inner_rect, border_radius=5)
        pygame.draw.line(surf, (40, 40, 50), (inner_rect.left, inner_rect.centery), (inner_rect.right, inner_rect.centery))
        
        if bits is None or len(bits) == 0: return
        
        # We'll plot about 8 bits worth of wave
        display_bits = bits[:8]
        pts_per_bit = 40
        total_pts = len(display_bits) * pts_per_bit
        
        # For alignment visualization
        for i in range(len(display_bits) + 1):
            lx = inner_rect.left + (i / len(display_bits)) * inner_rect.width
            pygame.draw.line(surf, (25, 25, 30), (lx, inner_rect.top), (lx, inner_rect.bottom), 1)

        points = []
        for i in range(total_pts):
            bit_idx = i // pts_per_bit
            t_in_bit = (i % pts_per_bit) / pts_per_bit
            
            # Phase calculation
            if mod_type == "BPSK":
                phase = 0 if display_bits[bit_idx] == 0 else np.pi
            else: # QPSK or others (simplify to phase shift)
                phase = (bit_idx % 4) * (np.pi/2)
                
            val = np.sin(2 * np.pi * t_in_bit + phase)
            
            if noise_snr is not None:
                snr_linear = 10**(noise_snr/10.0)
                std = np.sqrt(1.0 / snr_linear)
                val += np.random.normal(0, std * 0.6)
            
            px = inner_rect.left + (i / total_pts) * inner_rect.width
            py = inner_rect.centery - val * (inner_rect.height * 0.4)
            points.append((px, py))
            
        if len(points) > 1:
            color = (0, 255, 255) if noise_snr is None else (255, 120, 50)
            pygame.draw.lines(surf, color, False, points, 2)

    # --- Step-by-Step Flow ---
    flow_x = rect.x + 60
    flow_y = rect.y + 110
    step_h = 85
    
    # 1. Word -> Bits
    sample_txt = result['tx_txt'].split()[0] if result['tx_txt'] else "DAT"
    surface.blit(font.render(f"Seq 1: 文本采样与位流转换 [{sample_txt}]", True, ACCENT_COLOR), (flow_x, flow_y))
    draw_bit_grid(surface, (flow_x + 30, flow_y + 35), data['raw_bits'], "原始比特:")
    
    # Arrow
    pygame.draw.line(surface, (60, 70, 80), (flow_x + 15, flow_y + 65), (flow_x + 15, flow_y + 85), 2)
    
    # 2. Encoding
    flow_y += step_h
    surface.blit(font.render(f"Seq 2: 纠错力场装载 ({lbl_code})", True, ACCENT_COLOR), (flow_x, flow_y))
    draw_bit_grid(surface, (flow_x + 30, flow_y + 35), data['enc_bits'], "防护层数据:", (100, 255, 150))
    
    # Arrow
    pygame.draw.line(surface, (60, 70, 80), (flow_x + 15, flow_y + 65), (flow_x + 15, flow_y + 85), 2)
    
    # 3. Modulation
    flow_y += step_h
    surface.blit(font.render(f"Seq 3: 载波相位映射 ({lbl_mod})", True, ACCENT_COLOR), (flow_x, flow_y))
    wave_rect_tx = pygame.Rect(flow_x + 30, flow_y + 30, 420, 60)
    draw_waveform(surface, wave_rect_tx, data['raw_bits'], data['mod_type'])
    # Draw bits aligned below waveform
    for i, b in enumerate(data['raw_bits'][:8]):
        bx = wave_rect_tx.left + (i + 0.5) * (wave_rect_tx.width / 8)
        col = (0, 255, 200) if b == 1 else (100, 105, 115)
        t = label_font.render(str(int(b)), True, col)
        surface.blit(t, (bx - t.get_width()//2, wave_rect_tx.bottom + 5))

    # 4. Noise
    flow_y += step_h + 35
    surface.blit(font.render(f"Seq 4: Space Noise Injection", True, (255, 100, 100)), (flow_x, flow_y))
    wave_rect_rx = pygame.Rect(flow_x + 30, flow_y + 30, 420, 60)
    draw_waveform(surface, wave_rect_rx, data['raw_bits'], data['mod_type'], noise_snr=result['final_snr'])

    # 5. Demod / Decode
    flow_y += step_h
    surface.blit(font.render(f"Seq 5: Demodulation & Error Correction", True, ACCENT_COLOR), (flow_x, flow_y))
    
    # Fake error detection for visual feedback: compare dec_bits with raw_bits
    errors = []
    if data['raw_bits'] is not None and data['dec_bits'] is not None:
        min_len = min(len(data['raw_bits']), len(data['dec_bits']), 24)
        for i in range(min_len):
            # Since dec_bits is after correction, we can't easily show the "wrong" bit 
            # unless we captured demod_bits. Let's simulate a few "fixed" spots if not successful
            errors.append(data['raw_bits'][i] != data['dec_bits'][i])

    draw_bit_grid(surface, (flow_x + 30, flow_y + 35), data['dec_bits'], "最终输出:", (255, 215, 0), highlight_errors=errors if any(errors) else None)
    
    # 6. Final
    flow_y += step_h
    res_txt = result['rx_msg'].split()[0] if result['rx_msg'] else "???"
    surface.blit(font.render(f"Seq 6: 数据还原成果", True, SUCCESS_COLOR), (flow_x, flow_y))
    surface.blit(header_font.render(f"TEXT: [{res_txt}]", True, (255, 255, 255)), (flow_x + 30, flow_y + 30))

    # --- Right Side: Diagnostic Summary ---
    diag_rect = pygame.Rect(rect.x + 720, rect.y + 120, 330, 420)
    pygame.draw.rect(surface, (25, 30, 40), diag_rect, border_radius=10)
    pygame.draw.rect(surface, (60, 80, 110), diag_rect, 1, border_radius=10)
    surface.blit(font.render("未知建议 (Some Advisory)", True, (255, 215, 0)), (diag_rect.x + 20, diag_rect.y + 20))
    
    # Diagnostic content
    y_p = diag_rect.y + 60
    
    # NEW: Multi-hop summary
    if 'steps' in result and result['steps']:
        surface.blit(label_font.render("幻影回声跳跃 (Ghost Echo Hops):", True, (200, 200, 200)), (diag_rect.x + 20, y_p))
        y_p += 25
        for step in result['steps'][:5]: # Show up to 5 hops
            hop_color = (100, 255, 100) if step['snr'] > 5 else (255, 200, 0) if step['snr'] > -5 else (255, 100, 100)
            snr_val = step['snr']
            snr_str = f"{snr_val:.1f}dB" if snr_val > -900 else "BLOCKED"
            hop_txt = label_font.render(f"  {step['from']} -> {step['to']}: {snr_str}", True, hop_color)
            surface.blit(hop_txt, (diag_rect.x + 20, y_p))
            y_p += 20
        y_p += 10
        
    diag_msg = "本次传输状态: " + ("【优】" if result['success'] else "【警】") + "\n\n"
    if result['success']:
        # 使用翻译名优化战报文本
        diag_msg += f"Current scheme {data['code_type']} successfully corrected errors at {result['final_snr']:.1f}dB SNR. Relay gain was critical. Suggest maintaining current config."
    else:
        diag_msg += f"WARNING: {result['failure_reason']}\n\nSignal distortion observed mid-chain. Suggest checking node health or enabling high-gain modules."
    
    render_text_wrapped(surface, diag_msg, (diag_rect.x + 20, y_p), 290, label_font, TEXT_COLOR)

    close_btn.draw(surface)

def draw_tech_unlock_screen(surface, level, btn):
    surface.fill((10, 15, 20)) # Darker background
    if not level: return
    
    tech_info = level.get('tech_unlock_info') or {}
    
    # Title - Centered
    title = header_font.render(tech_info.get('title', 'Unknown Tech'), True, (100, 255, 100))
    mx = WINDOW_WIDTH // 2
    surface.blit(title, (mx - title.get_width()//2, 60))
    
    # Separator
    pygame.draw.line(surface, (50, 150, 50), (100, 100), (WINDOW_WIDTH - 100, 100), 2)
    
    y = 140
    
    # Image - Centered
    img_path = tech_info.get('image')
    if img_path:
        # Draw Image Centered
        draw_image_fit(surface, img_path, (mx, y + 150), (500, 300))
        y += 330 # Move down
    else:
        y += 20

    # Content Box - Centered & Widened
    box_width = WINDOW_WIDTH - 300
    box_x = (WINDOW_WIDTH - box_width) // 2
    
    # Calculate required height for text or use fixed height
    box_height = 400
    
    pygame.draw.rect(surface, (20, 25, 30), (box_x, y, box_width, box_height), border_radius=12)
    pygame.draw.rect(surface, (60, 80, 100), (box_x, y, box_width, box_height), 1, border_radius=12)

    # Text Content
    text_y = y + 30
    text_x = box_x + 40
    text_width = box_width - 80
    
    # Use larger font for description
    desc_font = header_font # Use header_font (size 32) instead of label_font/font
    
    full_text = ""
    if 'intro' in tech_info: full_text += tech_info['intro'] + "\n\n"
    if 'specs' in tech_info: full_text += tech_info['specs']
    
    render_text_wrapped(surface, full_text, (text_x, text_y), text_width, desc_font, (220, 220, 220))
    
    btn.draw(surface)

def draw_conclusion_screen(surface, level_id, btn):
    surface.fill((10, 15, 20)) # Darker background
    
    # Title
    title_text = "Phase I Analysis: BPSK vs QPSK"
    title_surf = header_font.render(title_text, True, ACCENT_COLOR) # Use game accent color
    mx = WINDOW_WIDTH // 2
    y_start = 60
    surface.blit(title_surf, (mx - title_surf.get_width()//2, y_start))
    
    # Separator
    pygame.draw.line(surface, (50, 150, 50), (100, y_start+40), (WINDOW_WIDTH - 100, y_start+40), 2)
    
    y = y_start + 60
    
    # Content Box - Centered & Widened
    box_width = WINDOW_WIDTH - 200
    box_x = (WINDOW_WIDTH - box_width) // 2
    box_height = 600
    
    pygame.draw.rect(surface, (20, 25, 30), (box_x, y, box_width, box_height), border_radius=12)
    pygame.draw.rect(surface, (60, 80, 100), (box_x, y, box_width, box_height), 1, border_radius=12)
    
    # Image - Left Side (60% width)
    img_path = "picture/compare_constellation.png"
    img_region_w = box_width * 0.65
    img_region_h = box_height - 40
    
    img_center_x = box_x + img_region_w / 2
    img_center_y = y + box_height / 2
    
    draw_image_fit(surface, img_path, (img_center_x, img_center_y), (img_region_w - 40, img_region_h))

    # Text Content - Right Side (Remaining width)
    text_x = box_x + img_region_w + 20
    text_y = y + 60
    text_width = box_width - img_region_w - 40
    
    desc_font = font # Use standard font
    
    # Paragraph 1
    para1 = "指挥官，您应该注意到了：虽然 QPSK 传输速度快了一倍，但在横跨大西洋的强噪声环境中，它的误码率急剧上升。"
    text_y = render_text_wrapped(surface, para1, (text_x, text_y), text_width, desc_font, (220, 220, 220))
    text_y += 30 
    
    # Paragraph 2
    para2 = "从右侧的星座图对比可以看出，QPSK 的四个信号点挤在一起，最小欧氏距离仅为 BPSK 的 0.7 倍，更容易被噪声挤出安全区。"
    text_y = render_text_wrapped(surface, para2, (text_x, text_y), text_width, desc_font, (220, 220, 220))
    text_y += 40
    
    # Conclusion
    para3 = "结论：在恶劣环境下，有时候“慢”就是“快”。BPSK 依然是可靠性之王。"
    conclusion_font = header_font # Bigger font for conclusion
    # Use simpler render since it's short and impactful
    # But wrap just in case
    render_text_wrapped(surface, para3, (text_x, text_y), text_width, conclusion_font, ACCENT_COLOR) # Use accent color for conclusion
    
    btn.draw(surface)

# --- Knowledge Base Logic（阶段三 3.3 改为技能树）---
g_knowledge_ui_rects = []
g_tech_tree_rects = []  # 技能树节点 [(rect, node_data), ...]

def build_knowledge_db(level_mgr):
    """仍用于详情页回退时保留列表；技能树从 level_mgr 直接构建。"""
    global g_knowledge_list
    g_knowledge_list = []
    seen_titles = set()
    def add_item(title, text, image, unlocked=True, original_level_id=0):
        if title in seen_titles: return
        seen_titles.add(title)
        g_knowledge_list.append({'title': title, 'text': text, 'image': image, 'unlocked': unlocked, 'level_id': original_level_id})
    for lvl in level_mgr.levels:
        if 'tutorial_slides' in lvl:
            for s in lvl['tutorial_slides']:
                add_item(s['title'], s['text'], s.get('image'), True, lvl.get('id', 0))
        if 'tech_unlock_info' in lvl:
            t = lvl['tech_unlock_info']
            full_text = t['intro'] + "\n\n" + t['specs']
            add_item(t['title'], full_text, t.get('image'), True, lvl.get('id', 0))

def draw_knowledge_menu(surface, btn_back, level_mgr, current_level_idx):
    """阶段三 3.3：相关知识页面改为技能树。"""
    global g_tech_tree_rects
    g_tech_tree_rects = draw_tech_tree_screen(
        surface, level_mgr, current_level_idx, btn_back,
        font, header_font, label_font,
        accent_color=ACCENT_COLOR, bg_color=BG_COLOR, text_color=TEXT_COLOR,
        width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
    )

def draw_knowledge_detail(surface, btn_back):
    surface.fill(BG_COLOR)
    
    item = g_current_knowledge_item
    if not item: 
        btn_back.draw(surface)
        return

    # Center Layout
    mx = WINDOW_WIDTH // 2
    
    # Title
    title = header_font.render(item['title'], True, ACCENT_COLOR)
    surface.blit(title, (mx - title.get_width()//2, 50))
    
    pygame.draw.line(surface, (50, 150, 50), (100, 100), (WINDOW_WIDTH-100, 100), 2)
    
    y = 130
    
    # Image - Centered
    if item.get('image'):
        # Try to fit image
        draw_image_fit(surface, item['image'], (mx, y + 150), (600, 300))
        y += 330
    else:
        y += 20
    
    # Text Content Box - Centered & Wide
    box_width = WINDOW_WIDTH - 300
    box_x = (WINDOW_WIDTH - box_width) // 2
    box_height = 400
    
    start_txt_y = y
    
    # Draw background for text
    pygame.draw.rect(surface, (20, 24, 30), (box_x, start_txt_y, box_width, box_height), border_radius=12)
    pygame.draw.rect(surface, (60, 65, 75), (box_x, start_txt_y, box_width, box_height), 1, border_radius=12)
    
    content = item['text']
    curr_y = start_txt_y + 30
    
    # Use larger font (header_font is usually ~32px, font is ~20px)
    # Let's use something in between or just header_font if it looks good
    # The user asked for "larger font"
    desc_font = header_font 
    
    # Use our wrapping function with centered box
    render_text_wrapped(surface, content, (box_x + 40, curr_y), box_width - 80, desc_font, TEXT_COLOR)

    btn_back.draw(surface)


# --- 阶段三 3.1 成就通知与成就列表界面（成就.md 4.3 + 上下滑动）---
def update_achievement_notification(ticks_ms):
    """更新成就小型通知状态：滑入→停留 2s→滑出，不阻塞；多个成就依次显示。"""
    global g_achievement_notif_state, g_achievement_popup_queue
    target_x = WINDOW_WIDTH - NOTIF_W - 24
    if g_achievement_notif_state is None:
        if not g_achievement_popup_queue:
            return
        ach_id = g_achievement_popup_queue.pop(0)
        g_achievement_notif_state = {
            "ach_id": ach_id,
            "phase": "slide_in",
            "start_ticks": ticks_ms,
            "x_offset": WINDOW_WIDTH,
        }
        return
    st = g_achievement_notif_state
    elapsed = ticks_ms - st["start_ticks"]
    if st["phase"] == "slide_in":
        t = min(1.0, elapsed / NOTIF_SLIDE_MS)
        # 缓动：ease-out
        t = 1.0 - (1.0 - t) ** 2
        st["x_offset"] = int(WINDOW_WIDTH + (target_x - WINDOW_WIDTH) * t)
        if elapsed >= NOTIF_SLIDE_MS:
            st["phase"] = "hold"
            st["start_ticks"] = ticks_ms
    elif st["phase"] == "hold":
        if elapsed >= NOTIF_HOLD_MS:
            st["phase"] = "slide_out"
            st["start_ticks"] = ticks_ms
    elif st["phase"] == "slide_out":
        t = min(1.0, elapsed / NOTIF_SLIDE_MS)
        t = t * t  # ease-in
        st["x_offset"] = int(target_x + (WINDOW_WIDTH - target_x) * t)
        if elapsed >= NOTIF_SLIDE_MS:
            g_achievement_notif_state = None
            # 立即检查队列，下一帧会显示下一个
            return update_achievement_notification(ticks_ms)


def draw_achievement_notification(surface, font_obj, label_font_obj):
    """绘制右上角小型成就通知（成就.md 4.3）：从右侧滑入，停留 2 秒后滑出。"""
    global g_achievement_notif_state
    if g_achievement_notif_state is None:
        return
    st = g_achievement_notif_state
    ach = g_achievement_manager.get_achievement(st["ach_id"])
    if not ach:
        g_achievement_notif_state = None
        return
    x = st["x_offset"]
    y = 24
    # 小型通知框
    s = pygame.Surface((NOTIF_W, NOTIF_H), pygame.SRCALPHA)
    s.fill((22, 28, 36, 248))
    pygame.draw.rect(s, ACCENT_COLOR, s.get_rect(), 2, border_radius=10)
    surface.blit(s, (x, y))
    # 🎉 成就解锁！
    title_surf = label_font_obj.render("成就解锁！", True, (255, 200, 50))
    surface.blit(title_surf, (x + 16, y + 12))
    # 图标/图片 + 名称：有隐藏成就图片则显示图片，否则用 emoji 图标
    img_rel = ach.get("image")
    name_x = x + 16
    if img_rel:
        img_surf = load_achievement_image(img_rel, 44, 44)
        if img_surf:
            surface.blit(img_surf, (name_x, y + 34))
            name_x += 52
    name_surf = font_obj.render((ach["icon"] + " " if not img_rel else "") + ach["name"], True, (255, 255, 255))
    surface.blit(name_surf, (name_x, y + 38))


def draw_achievements_screen(surface, btn_back):
    """成就列表界面：分类、进度条、已解锁/未解锁列表；支持上下滑动（成就.md 4.2 + 滑动）。"""
    global g_achievement_scroll_y
    surface.fill(BG_COLOR)
    unlocked_count, total_count = g_achievement_manager.get_progress()
    # 标题与进度（固定）
    t_surf = header_font.render("成就系统", True, ACCENT_COLOR)
    surface.blit(t_surf, (WINDOW_WIDTH // 2 - t_surf.get_width() // 2, 30))
    prog_str = f"进度: {unlocked_count} / {total_count}"
    surface.blit(font.render(prog_str, True, TEXT_COLOR), (WINDOW_WIDTH // 2 - 80, 75))
    # 进度条
    bar_w = 400
    bar_x = WINDOW_WIDTH // 2 - bar_w // 2
    pygame.draw.rect(surface, (40, 45, 55), (bar_x, 105, bar_w, 18), border_radius=4)
    pct = unlocked_count / total_count if total_count else 0
    pygame.draw.rect(surface, ACCENT_COLOR, (bar_x, 105, int(bar_w * pct), 18), border_radius=4)
    pygame.draw.rect(surface, (60, 70, 85), (bar_x, 105, bar_w, 18), 1, border_radius=4)
    # 列表区域：可滚动，可见高度从 130 到 返回按钮上方
    list_top = 130
    list_bottom = WINDOW_HEIGHT - 90
    visible_h = list_bottom - list_top
    # 先计算总内容高度
    content_y = 0
    for category, cat_name in CATEGORY_NAMES.items():
        items = g_achievement_manager.get_by_category(category)
        if not items:
            continue
        content_y += 28
        content_y += len(items) * 62
        content_y += 12
    max_scroll = max(0, content_y - visible_h)
    g_achievement_scroll_y = max(0, min(g_achievement_scroll_y, max_scroll))
    # 裁剪并绘制列表
    clip_rect = pygame.Rect(0, list_top, WINDOW_WIDTH, visible_h)
    surface.set_clip(clip_rect)
    y = list_top - g_achievement_scroll_y
    for category, cat_name in CATEGORY_NAMES.items():
        items = g_achievement_manager.get_by_category(category)
        if not items:
            continue
        surface.blit(font.render(cat_name, True, (150, 180, 220)), (80, y))
        y += 28
        for ach_id, ach_data in items.items():
            unlocked = ach_id in g_achievement_manager.unlocked
            name = ach_data["name"] if unlocked or not ach_data.get("hidden") else "???"
            desc = ach_data["desc"] if unlocked or not ach_data.get("hidden") else "???"
            icon = ach_data["icon"] if unlocked or not ach_data.get("hidden") else "🔒"
            color = (220, 220, 220) if unlocked else (120, 120, 130)
            r = pygame.Rect(80, y, WINDOW_WIDTH - 160, 56)
            pygame.draw.rect(surface, (28, 32, 40), r, border_radius=6)
            pygame.draw.rect(surface, (50, 60, 75), r, 1, border_radius=6)
            # 已解锁且存在隐藏成就图片时显示图片，否则显示图标
            text_x = 100
            if unlocked and ach_data.get("image"):
                img_surf = load_achievement_image(ach_data["image"], 48, 48)
                if img_surf:
                    surface.blit(img_surf, (100, y + 4))
                    text_x = 158
            name_text = (f"{icon} " if text_x == 100 else "") + name
            surface.blit(font.render(name_text, True, color), (text_x, y + 8))
            surface.blit(label_font.render(desc, True, (150, 160, 170)), (100, y + 32))
            status = "已解锁" if unlocked else "未解锁"
            surface.blit(label_font.render(status, True, (100, 200, 120) if unlocked else (100, 100, 110)), (r.right - 90, y + 18))
            y += 62
        y += 12
    surface.set_clip(None)
    # 滚动提示（当可滚动时）
    if max_scroll > 0:
        hint = label_font.render("滚轮上下滑动", True, (100, 120, 140))
        surface.blit(hint, (WINDOW_WIDTH - hint.get_width() - 24, list_bottom - 22))
    btn_back.draw(surface)


# --- Hidden Level Logic ---
def generate_hidden_satellite_level():
    # 4 rows, 5 cols
    # Randomized status: 3 'good' total, max 1 per row. 
    # Row indices: 0, 1, 2, 3
    
    rows = 4
    cols = 5
    # good_total = 3 is ensured by picking 3 unique rows
    
    # Assign which rows get a good sat
    # Pick 3 unique rows from 4
    good_rows = np.random.choice(range(rows), 3, replace=False)
    
    # Grid structure
    nodes = []
    
    # 将中心 X 坐标设为地图区域的中心 (MAP_WIDTH // 2)
    # MAP_WIDTH 是 1020，所以中心约为 510
    map_center_x = MAP_WIDTH // 2
    
    # Source (Earth Connection)
    nodes.append({"name": "Earth Link", "pos": (map_center_x, 700), "type": "src", "status": "normal"})
    
    # Array Generation (Sector)
    # Center at (map_center_x, 850) (Below screen), radiating upwards
    center_x, center_y = map_center_x, 850
    base_radius = 200
    radius_step = 100
    angle_start = -np.pi * 0.8 # Left
    angle_end = -np.pi * 0.2 # Right
    angle_step = (angle_end - angle_start) / (cols - 1)
    
    for r in range(rows):
        # Determine if this row has a good sat
        has_good = r in good_rows
        good_col = -1
        if has_good:
            good_col = np.random.randint(0, cols)
            
        current_radius = base_radius + r * radius_step
        
        for c in range(cols):
            angle = angle_start + c * angle_step
            # Add some jitter
            jitter_a = np.random.uniform(-0.05, 0.05)
            jitter_r = np.random.uniform(-10, 10)
            
            px = center_x + (current_radius + jitter_r) * np.cos(angle + jitter_a)
            py = center_y + (current_radius + jitter_r) * np.sin(angle + jitter_a)
            
            # Status
            if c == good_col:
                status = "good" 
            else:
                status = "damaged"
                
            # 隐藏模式：不显示卫星好坏
            name = f"Sat-{r+1}-{c+1}"
                
            nodes.append({
                "name": name,
                "pos": (px, py),
                "type": "relay",
                "status": status
            })

    # Destination (Core)
    nodes.append({"name": "Array Core", "pos": (map_center_x, 100), "type": "dest", "status": "normal"})

    return {
        "id": "HIDDEN_SAT_ARRAY",
        "title": "遗落的矩阵",
        "phase": "Hidden: 尘封的记忆",
        "story_intro": "这是一个被遗忘的近地卫星阵列。\n由于电池组老化，阵列仅剩微弱的备用能源。\n一旦高能信号激发，供电平衡将被打破。",
        "mission_info": f"【系统限制】\n1. 能量瓶颈：你只有 {MAX_HIDDEN_ATTEMPTS} 次发射信号的机会，随后阵列将因过载关闭。\n2. 链路极不稳定：为了维持相位同步，中转站数量必须严格控制在 2-3 个节点。",
        "mission_text": f"目标：在 {MAX_HIDDEN_ATTEMPTS} 次尝试内，找出包含 2 或 3 个完好中转站的通信路径。",
        "message": "ANCIENT_ARRAY_ONLINE",
        "message_desc": "[矩阵重启]",
        "snr_mode": "distance", # Custom logic inside calc_snr overrides this partially
        "tx_power": 60, 
        "available_mods": ["BPSK", "QPSK"],
        "available_codes": ["Hamming(7,4)", "Polar"],
        "target_ber": 0.0, 
        "reward": "隐藏关卡完成：解锁信号增强器 (+6dB 全局被动)",
        "source_name": "Earth Link", "dest_name": "Array Core",
        "source_pos": (map_center_x, 700), "dest_pos": (map_center_x, 100),
        "nodes": nodes
    }

# Ghost Cube State
ghost_cube_timer = 0
ghost_cube_visible = False
ghost_cube_pos = (200, 650) # Near Earth in L10
ghost_cube_rect = pygame.Rect(0,0, 30, 30)

# --- 游戏平衡参数 ---
MAX_HIDDEN_ATTEMPTS = 5 # 隐藏关最大尝试次数
num_repaired_satellites = 0 # Track how many good sats found in Hidden Level

def update_ghost_cube(dt, current_level_id):
    global ghost_cube_timer, ghost_cube_visible, ghost_cube_pos
    
    # 仅在碎石带第一关 (Level 8) 出现，且访问过就不再出现
    if current_level_id != 8 or g_hidden_level_visited: 
        ghost_cube_visible = False
        return

    ghost_cube_timer += dt  # dt is ms
    
    cycle = 10000 # 10s
    show = 2000 # 2s
    
    mod_time = ghost_cube_timer % cycle
    
    # Circular Orbit around Earth (100, 700)
    # Radius ~80, Period ~5s (independent of visibility cycle to make it appear at diff spots)
    orbit_t = ghost_cube_timer * 0.001 # seconds
    center = (100, 700)
    radius = 80
    
    # Smooth orbital movement
    gx = center[0] + radius * np.cos(orbit_t)
    gy = center[1] + radius * np.sin(orbit_t)
    ghost_cube_pos = (gx, gy)
    
    if mod_time < show:
        ghost_cube_visible = True
        # Visual Glitch: Only flicker visibility/alpha, not position
        # Handled in draw (alpha) or here? 
        # Requirement: "Don't shake randomly". So we rely on smooth path.
    else:
        ghost_cube_visible = False
        
    ghost_cube_rect.topleft = ghost_cube_pos

def draw_ghost_cube(surface):
    if not ghost_cube_visible: return
    
    # Draw blurred square
    # Visual: Glitchy cyan box
    s = pygame.Surface((30, 30), pygame.SRCALPHA)
    s.fill((0, 255, 255, 100)) # Semi-transparent
    surface.blit(s, ghost_cube_pos)
    pygame.draw.rect(surface, (200, 255, 255), (*ghost_cube_pos, 30, 30), 1)

# --- APP ---
def main():
    global current_state, previous_state, g_letter_scroll_idx, g_intro_alpha, g_intro_timer, g_level_stars
    
    # 加载存档（关卡进度、星级、游戏统计、成就）
    global g_game_stats, g_achievement_manager
    loaded = load_progress()
    if loaded:
        level_mgr.current_level_idx = min(loaded[0], len(level_mgr.levels) - 1)
        g_level_stars = loaded[1] if isinstance(loaded[1], dict) else {}
        if loaded[2] is not None and isinstance(loaded[2], dict):
            def_stats = _default_game_stats()
            def_stats.update(loaded[2])
            if "tried_combinations" in loaded[2] and isinstance(loaded[2]["tried_combinations"], list):
                def_stats["tried_combinations"] = loaded[2]["tried_combinations"]
            g_game_stats.update(def_stats)
        if loaded[3] is not None:
            g_achievement_manager.load(loaded[3])
    
    current_mod = "BPSK"
    current_code = "None"
    selected_protocol = "udp"
    
    # New: Polar Decoding Method Selection
    current_polar_method = "SC" # Default
    
    # Budget-driven tech system (remove reactor energy)
    has_laser_tech = False # 初始不可用，需解锁
    has_satellite_array_tech = False # 保持 False，等待玩家触发隐藏关
    laser_module_active = False # Toggle state
    
    sim_result = None
    level_complete = False
    show_analysis = False
    
    is_animating = False
    anim_progress = 0.0
    transmission_stats_until = 0  # 传输完成统计覆盖层 (2.3)
    
    ui_mod_rects = []
    ui_code_rects = []
    ui_protocol_rects = []
    weather_cycle_rect = pygame.Rect(0, 0, 0, 0)
    hud_scroll_y = 0
    hud_scroll_max = 0
    sat_deployment = None
    sat_network = None
    sat_selected_type = "basic"
    sat_selected_pos = None
    sat_message = ""
    frame_counter = 0
    command_mode = False
    command_buffer = ""
    command_feedback = ""
    command_feedback_until = 0
    causal_animation = None
    causal_pending_send = False
    
    # UI Rects for decoding methods
    ui_decoder_rects = []
    ui_tech_rects = []

    # New State Variables
    path_indices = [] # Stores indices of nodes in level['nodes']
    hidden_attempts = 0 # 隐藏关尝试次数
    
    # Dynamic Node Management
    # To prevent polluting the original levels.py data, we need to deep copy nodes when mission starts.
    import copy
    budget_manager = BudgetManager(initial_budget=1000)
    weather_system = WeatherSystem()
    protocol_system = ProtocolSystem()
    power_slider = PowerSlider(MAP_WIDTH + 40, 0, HUD_WIDTH - 80, min_power=10.0, max_power=70.0, current_power=30.0)
    segmented_transmission = None

    def assign_pending_weather(level_obj):
        if isinstance(level_obj, dict):
            level_obj["pending_weather"] = random.choice(["clear", "cloudy", "rain", "storm", "solar_flare"])

    def should_open_satellite_deployment(level_obj):
        if not isinstance(level_obj, dict):
            return False
        dep = level_obj.get("satellite_deployment", {}) or {}
        return bool(dep.get("enabled", False))

    def cb_new_game():
        """新游戏：覆盖存档并从第一关开场开始"""
        global current_state, g_intro_alpha, g_intro_timer, g_level_stars, g_game_stats, g_achievement_manager
        g_game_stats = _default_game_stats()
        g_achievement_manager.unlocked.clear()
        save_progress(0, {}, g_game_stats, g_achievement_manager.save())
        level_mgr.current_level_idx = 0
        g_level_stars = {}
        current_state = STATE_INTRO_1
        g_intro_alpha = 0
        g_intro_timer = 0
        play_bgm(None)

    def cb_continue_game():
        """继续游戏：读取本地存档并进入关卡目录"""
        global current_state, g_level_stars, g_game_stats, g_achievement_manager
        loaded = load_progress()
        if loaded:
            level_mgr.current_level_idx = min(loaded[0], len(level_mgr.levels) - 1)
            g_level_stars = loaded[1] if isinstance(loaded[1], dict) else {}
            if loaded[2] is not None and isinstance(loaded[2], dict):
                def_stats = _default_game_stats()
                def_stats.update(loaded[2])
                g_game_stats.update(def_stats)
            if loaded[3] is not None:
                g_achievement_manager.load(loaded[3])
        else:
            level_mgr.current_level_idx = 0
            g_level_stars = {}
        current_state = STATE_LEVEL_CATALOG
        play_bgm("ofeliasdream.mp3")

    def cb_open_level_catalog():
        global current_state
        current_state = STATE_LEVEL_CATALOG
        play_bgm("ofeliasdream.mp3")

    def cb_catalog_back():
        global current_state
        current_state = STATE_START_SCREEN

    def cb_skip_intro():
        # 跳过开场直接进 BRIEFING
        global current_state, g_intro_alpha, g_intro_timer
        
        current_state = STATE_BRIEFING
    
        # Init first level logic
        level = level_mgr.get_current_level()
        if level:
            assign_pending_weather(level)
            play_bgm(get_level_music(level.get('id', 0)))

    def start_level_play():
        nonlocal has_satellite_array_tech, hidden_attempts, sim_result, is_animating, path_indices, has_laser_tech, current_mod, current_code, selected_protocol, segmented_transmission, hud_scroll_y, sat_deployment, sat_network, sat_selected_pos, sat_message, causal_animation, causal_pending_send
        global current_state, g_letter_scroll_idx, g_level_start_time

        g_level_start_time = pygame.time.get_ticks()
        sim_result = None
        is_animating = False
        path_indices = []
        hidden_attempts = 0 # 进入关卡重置尝试次数

        lvl = level_mgr.get_current_level()
        if not lvl:
            return
        # 首次通关判定：进入关卡时若从未记录，则默认“首次挑战仍成立”
        if isinstance(lvl.get("id"), int):
            key = str(lvl.get("id"))
            global g_game_stats
            ft = g_game_stats.get("level_first_try", {}) or {}
            if key not in ft:
                ft[key] = True
            g_game_stats["level_first_try"] = ft

        # 第一关教学：不预设调制，让玩家按教程步骤点击 BPSK，避免该步被直接跳过；编码固定为 None（第一关无编码选项）
        if lvl.get('id') == 1:
            g_tutorial.start()
            current_mod = None
            current_code = "None"
        else:
            current_mod = lvl['available_mods'][0] if lvl.get('available_mods') else "BPSK"
            current_code = lvl.get('available_codes', ["None"])[0]

        selected_protocol = "udp"
        segmented_transmission = None
        hud_scroll_y = 0
        sat_deployment = None
        sat_network = None
        sat_selected_pos = None
        sat_message = ""
        causal_animation = None
        causal_pending_send = False
        if isinstance(lvl.get("id"), int):
            budget_manager.reset_level()
            weather_system.set_weather(lvl.get("pending_weather", "clear"))
            recommendations = recommend_tech_combo(lvl, weather_system.current_weather)
            if recommendations and current_mod in ("BPSK", "QPSK"):
                rec_mod = recommendations[0].get("modulation")
                rec_code = recommendations[0].get("coding")
                if rec_mod in lvl.get("available_mods", []):
                    current_mod = rec_mod
                if rec_code in lvl.get("available_codes", []):
                    current_code = rec_code
        
        try:
            lvl_id = int(lvl.get('id', 1))
        except:
            lvl_id = 999
            
        if isinstance(lvl_id, int) and lvl_id >= 7:
            has_laser_tech = True
            
        if 'nodes' in lvl:
            # Deep copy or ensure origin_pos is set. Since we modify nodes list, be careful.
            # Ideally reset nodes from backup if needed, but here we just patch.
            for node in lvl['nodes']:
                 if 'origin_pos' not in node:
                     node['origin_pos'] = node['pos']
            
            # Add dynamic satellite if needed
            if has_satellite_array_tech and isinstance(lvl_id, int):
                pos_to_add = None
                
                if lvl_id in [8, 9]:
                     pos_to_add = (100, 320) 
                elif lvl_id == 10:
                     pos_to_add = (140, 620)
                
                if pos_to_add:
                    exists = False
                    for n in lvl['nodes']:
                        if n.get('is_ancient_relay'): exists = True; break
                    
                    if not exists:
                        lvl['nodes'].append({
                            "name": "Sat-X (Ancient)",
                            "pos": pos_to_add,
                            "origin_pos": pos_to_add,
                            "type": "relay",
                            "is_ancient_relay": True
                        })
        
        # Check if we should show the letter view first
        if 'message' in lvl and lvl['message']:
            g_letter_scroll_idx = 0
            current_state = STATE_LETTER_VIEW
        else:
            current_state = STATE_PLAYING

        # Check Tutorial Trigger (If Level 1)
        if lvl_id == 1:
            g_tutorial.start()
        else:
            g_tutorial.active = False

    def start_edu_showcase():
        global current_state, g_edu_slides, g_edu_slide_idx
        lvl = level_mgr.get_current_level()
        if not lvl:
            return False
        slides = lvl.get('tutorial_slides')
        if slides and not lvl.get('tutorial_seen'):
            g_edu_slides = slides
            g_edu_slide_idx = 0
            lvl['tutorial_seen'] = True
            current_state = STATE_EDU_SHOWCASE
            return True
        return False

    def proceed_to_mission_start():
        if start_edu_showcase():
            return
        start_level_play()

    def start_satellite_deployment():
        nonlocal sat_deployment, sat_network, sat_selected_type, sat_selected_pos, sat_message
        global current_state
        lvl = level_mgr.get_current_level()
        if not lvl:
            return False
        sat_deployment = SatelliteDeployment(lvl, budget_manager.current_budget)
        sat_network = DynamicNetwork(lvl)
        sat_selected_type = "basic"
        sat_selected_pos = None
        sat_message = "提示：先在可部署区域点击位置，再点“确认发射”。"
        current_state = STATE_SATELLITE_DEPLOYMENT
        return True

    def cb_start_mission():
        lvl = level_mgr.get_current_level()
        if should_open_satellite_deployment(lvl):
            start_satellite_deployment()
            return
        proceed_to_mission_start()

    def cb_next_edu_slide():
        global g_edu_slide_idx
        if not g_edu_slides:
            start_level_play()
            return
        g_edu_slide_idx += 1
        if g_edu_slide_idx >= len(g_edu_slides):
            start_level_play()
    
    def update_planet_dynamics(level):
        """Calculates new positions for nodes based on time."""
        if 'nodes' not in level: return
        
        t = pygame.time.get_ticks() / 1000.0 # Time in seconds
        
        # Level 7 (轨道突围): Escape Velocity - Orbital Mechanics
        if level['id'] == 7:
            # Nodes: 
            # 0:Earth(Static), 1:Orbital(Orbit Earth), 2:DebrisA(Chaos), 
            # 3:L1(Lissajous), 4:LunarOrbit(Orbit Moon), 5:DebrisB(Chaos), 6:Luna(Static)
            
            # Earth (Index 0) - Static anchor
            earth_pos = level['nodes'][0]['origin_pos']
            
            # 1. Orbital Station (Index 1) - Low Earth Orbit (Elliptical)
            # Center: Earth, Radius: ~200px, Speed: Fast
            node = level['nodes'][1]
            bx, by = earth_pos
            angle = t * 0.5 
            node['pos'] = (bx + 200 * np.cos(angle), by + 150 * np.sin(angle))
            
            # 2. Debris Field Alpha (Index 2) - Chaotic Drift
            node = level['nodes'][2]
            ox, oy = node['origin_pos']
            node['pos'] = (ox + 20 * np.sin(t*1.2) + 10 * np.cos(t*2.5), 
                           oy + 20 * np.cos(t*1.5) + 5 * np.sin(t*3.0))

            # 3. Lagrange L1 (Index 3) - Lissajous (Figure-8)
            node = level['nodes'][3]
            ox, oy = node['origin_pos']
            # Figure-8 movement
            node['pos'] = (ox + 50 * np.sin(t * 0.4), 
                           oy + 30 * np.sin(t * 0.8))

            # Moon (Index 6) - Static anchor for local orbits
            moon_pos = level['nodes'][6]['origin_pos']

            # 4. Lunar Orbit (Index 4) - Retrograde Orbit around Moon
            node = level['nodes'][4]
            mx, my = moon_pos
            angle_m = -t * 0.3 # Negative for retrograde
            node['pos'] = (mx + 150 * np.cos(angle_m), my + 150 * np.sin(angle_m))

            # 5. Debris Field Beta (Index 5) - High Frequency Jitter
            node = level['nodes'][5]
            ox, oy = node['origin_pos']
            node['pos'] = (ox + 15 * np.sin(t*2.0 + 1), oy + 15 * np.cos(t*1.8))
        
        # Level 9 (碎石带): Asteroid Maze - Dynamic Obstacles
        elif level['id'] == 9:
            # 1. Update Relay Nodes (Orbiting Central Probe)
            # Center Probe (Index 3) - Static
            cx, cy = level['nodes'][3]['origin_pos']
            
            # Belt Outpost Alpha (Index 1)
            node = level['nodes'][1]
            angle1 = t * 0.2
            node['pos'] = (cx + 300 * np.cos(angle1), cy + 200 * np.sin(angle1))
            
            # Belt Outpost Beta (Index 2) - Opposite Phase
            node = level['nodes'][2]
            angle2 = t * 0.2 + np.pi
            node['pos'] = (cx + 300 * np.cos(angle2), cy + 200 * np.sin(angle2))
            
            # Comet 67P (Index 4) - Elliptical passing through
            node = level['nodes'][4]
            # Moves back and forth or large orbit
            ox, oy = node['origin_pos']
            node['pos'] = (ox + 50 * np.sin(t*0.5), oy + 100 * np.cos(t*0.5))

            # 2. Update Obstacles (Procedural Generation if needed)
            if 'obstacles' not in level:
                level['obstacles'] = []
                # Create a belt of asteroids (Reduced: Close to 8-10 pieces)
                # Using 2 rings instead of 3, with 4-5 per ring
                for r in [180, 260]:
                    count = 5 
                    for i in range(count):
                        theta_start = (2 * np.pi / count) * i
                        level['obstacles'].append({
                            # Dynamic props
                            'orbit_r': r,
                            'theta_start': theta_start,
                            'speed': (0.3 if r % 200 == 0 else -0.2) * (1.0 + np.random.rand()*0.2), 
                            'size': np.random.randint(15, 35),
                            'pos': [0,0] # Mutable
                        })
            
            # Update Obstacle positions
            for obs in level['obstacles']:
                # Orbit around Center Probe
                angle = obs['theta_start'] + obs['speed'] * t
                obs['pos'] = (
                    cx + obs['orbit_r'] * np.cos(angle),
                    cy + obs['orbit_r'] * np.sin(angle)
                )

        # Level 10 (深渊凝视): The Void (Kuiper Belt)
        elif level['id'] == 10:
            # Nodes: 0:Unified Array(Static), 1:Kuiper A, 2:Kuiper B, 3:Oort, 4:Deep Space, 5:The Void(Dest)
            
            # Center (Unified Array) - Static
            cx, cy = level['nodes'][0]['origin_pos']
            
            # Kuiper Belt Objects (Elliptical Orbits with Precession)
            # Node 1
            node = level['nodes'][1]
            a, b = 300, 150 # Ellipse radii
            angle = t * 0.15
            node['pos'] = (cx + a * np.cos(angle), cy + b * np.sin(angle))
            
            # Node 2 (Opposite phase, slightly different orbit)
            node = level['nodes'][2]
            a, b = 320, 180
            angle = t * 0.12 + np.pi
            node['pos'] = (cx + a * np.cos(angle), cy + b * np.sin(angle))
            
            # Oort Cloud (Node 3) - Very slow drift
            node = level['nodes'][3]
            ox, oy = node['origin_pos']
            node['pos'] = (ox + 50 * np.sin(t * 0.05), oy + 50 * np.cos(t * 0.04))
            
            # Deep Space Buoy (Node 4) - Floating
            node = level['nodes'][4]
            ox, oy = node['origin_pos']
            node['pos'] = (ox + 20 * np.sin(t * 0.2), oy + 20 * np.cos(t * 0.15))
            
            # Obstacles: Dense Ice Fields (Kuiper Debris)
            if 'obstacles' not in level:
                level['obstacles'] = []
                # Procedural generation of debris field (Reduced: 9 pieces)
                for i in range(9):
                    cx_obs = cx + np.random.randint(-100, 100) # Debris center variation
                    cy_obs = cy + np.random.randint(-50, 50)
                    level['obstacles'].append({
                        'pos': [0,0],
                        'orbit_r': np.random.randint(200, 500), # Wide band
                        'angle_start': np.random.rand() * 2 * np.pi,
                        'speed': (0.1 if i % 2 == 0 else -0.05) * (0.8 + np.random.rand()*0.4),
                        'size': np.random.randint(5, 12), # Small chunks
                         'center': (cx_obs, cy_obs)
                    })
            
            # Update Obstacles
            for obs in level['obstacles']:
                angle = obs['angle_start'] + obs['speed'] * t
                obs['pos'] = (
                    obs['center'][0] + obs['orbit_r'] * np.cos(angle),
                    obs['center'][1] + obs['orbit_r'] * np.sin(angle) * 0.6 # Flattened
                )
        
        # Level 11 (昆仑): Kunlun (Solar System)
        elif level['id'] == 11:
            # Nodes: 0:KUNLUN(Src), 1:Defense Sat, 2:Jovian Relay, 3:Mars, 4:Moon, 5:EARTH(Dest)
            
            # Node 5 (EARTH) - Static Anchor (Bottom Left)
            ex, ey = level['nodes'][5]['origin_pos']
            
            # Node 4 (Moon Base) - Orbits Earth
            node = level['nodes'][4]
            angle_m = t * 0.8
            node['pos'] = (ex + 100 * np.cos(angle_m), ey + 100 * np.sin(angle_m))
            
            # Node 3 (Mars Outpost) - Independent Orbit around Sun (simulated center)
            # Simulated Sun Center for visual context
            sun_x, sun_y = 600, 400
            
            node = level['nodes'][3]
            mx, my = node['origin_pos']
            # Mars moves in a wide arc
            node['pos'] = (mx + 30 * np.sin(t * 0.1), my + 10 * np.cos(t * 0.1)) 
            
            # Node 2 (Jovian Relay) - Jupiter Orbit System
            node = level['nodes'][2]
            jx, jy = node['origin_pos']
            node['pos'] = (jx + 20 * np.sin(t*0.05), jy + 20 * np.cos(t*0.05))
            
            # Node 0 (KUNLUN) - Far Out, Static position but internal rotation visual
            kx, ky = level['nodes'][0]['origin_pos']
            
            # Node 1 (Defense Sat Alpha) - Orbits KUNLUN
            node = level['nodes'][1]
            angle_k = t * 0.4
            node['pos'] = (kx + 120 * np.cos(angle_k), ky + 80 * np.sin(angle_k))
            
            # Obstacles: Solar Storms / Defense Swarms
            if 'obstacles' not in level:
                level['obstacles'] = []
                # 1. Swarm around Kunlun (Reduced: 4 pieces)
                for i in range(4):
                    level['obstacles'].append({
                        'type': 'swarm',
                        'center': (kx, ky),
                        'orbit_r': 180,
                        'angle_start': (2*np.pi/4)*i,
                        'speed': 0.5,
                        'size': 8,
                        'pos': [0,0]
                    })
                # 2. Solar Storm (Center Screen) (Reduced: 5 pieces)
                for i in range(5):
                    level['obstacles'].append({
                        'type': 'solar',
                        'center': (600, 400),
                        'orbit_r': np.random.randint(100, 350),
                        'angle_start': np.random.rand() * 2 * np.pi,
                        'speed': 0.1 * (1 if i%2==0 else -1),
                        'size': np.random.randint(15, 30),
                        'pos': [0,0]
                    })

            for obs in level['obstacles']:
                angle = obs['angle_start'] + obs['speed'] * t
                obs['pos'] = (
                    obs['center'][0] + obs['orbit_r'] * np.cos(angle),
                    obs['center'][1] + obs['orbit_r'] * np.sin(angle) * (0.8 if obs.get('type')=='solar' else 1.0)
                )

    def is_los_blocked(level, p1, p2):
        if 'obstacles' not in level: return False
        
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2-x1, y2-y1
        line_len_sq = dx*dx + dy*dy
        if line_len_sq == 0: return False

        for obs in level['obstacles']:
            ox, oy = obs['pos']
            r = obs['size'] + 5 # Hitbox margin
            
            # Project obstacle center onto line segment
            # t = dot(P1->Obs, P1->P2) / |P1->P2|^2
            t = ((ox - x1) * dx + (oy - y1) * dy) / line_len_sq
            t = max(0, min(1, t))
            
            cx, cy = x1 + t*dx, y1 + t*dy
            dist_sq = (ox - cx)**2 + (oy - cy)**2
            
            if dist_sq < r*r:
                return True
        return False

    def cb_finish_tech_unlock():
        global current_state, g_tech_unlock_level, g_level_start_time
        # 如果是从隐藏关卡退出并解锁技术，弹窗后直接回到那一关（PLAYING），而不是再进一次Briefing
        if g_tech_unlock_level and g_tech_unlock_level.get('tech_unlock_info', {}).get('title', '').startswith("阵列扫描"):
            current_state = STATE_PLAYING
            g_level_start_time = pygame.time.get_ticks()
        else:
            current_state = STATE_BRIEFING
            assign_pending_weather(level_mgr.get_current_level())
    
    def toggle_laser():
        nonlocal laser_module_active, sim_result
        if has_laser_tech:
            laser_module_active = not laser_module_active
            sim_result = None # Clear result

    def set_mod(mod):
        nonlocal current_mod, sim_result, is_animating
        if current_mod != mod:
            current_mod = mod
            sim_result = None
            is_animating = False

    def set_code(code):
        nonlocal current_code, sim_result, is_animating
        if current_code != code:
            current_code = code
            sim_result = None
            is_animating = False

    def set_protocol(protocol_id):
        nonlocal selected_protocol, sim_result, is_animating
        if selected_protocol != protocol_id:
            selected_protocol = protocol_id
            sim_result = None
            is_animating = False

    def set_polar_method(method):
        nonlocal current_polar_method, sim_result
        if current_polar_method != method:
            current_polar_method = method
            sim_result = None

    def build_causal_chain_config(level):
        if not level or current_mod is None or current_code is None:
            return None

        path_snrs = []
        if "nodes" in level and path_indices and len(path_indices) >= 2:
            for i in range(len(path_indices) - 1):
                idx_a = path_indices[i]
                idx_b = path_indices[i + 1]
                node_a = level["nodes"][idx_a]
                node_b = level["nodes"][idx_b]
                path_snrs.append(
                    calculate_path_snr(
                        node_a["pos"],
                        node_b["pos"],
                        power_slider.current_power,
                        level=level,
                        idx1=idx_a,
                        idx2=idx_b,
                    )
                )
        base_snr = (sum(path_snrs) / len(path_snrs)) if path_snrs else (7.5 + compute_power_snr_boost(power_slider.current_power))

        mod_effect_map = {"BPSK": 0.9, "QPSK": 0.0, "8PSK": -1.1, "16QAM": -1.8}
        mod_effect = mod_effect_map.get(current_mod, -1.3)

        if current_code == "None":
            code_effect = 0.0
        elif current_code.startswith("Repetition"):
            code_effect = 0.9
        elif current_code.startswith("Hamming"):
            code_effect = 1.5
        elif current_code.startswith("Polar"):
            code_effect = 2.6
        else:
            code_effect = 0.8

        weather_info = weather_system.get_weather_info()
        weather_effect = weather_info.snr_penalty
        if laser_module_active:
            weather_effect += weather_info.laser_penalty
        if "Polar" in current_code:
            weather_effect += weather_info.polar_boost

        proto_info = protocol_system.get_protocol_info(selected_protocol)
        final_snr = base_snr + mod_effect + code_effect + weather_effect
        success_rate = max(0.05, min(0.98, (final_snr + 2.0) / 16.0))
        success_rate *= max(0.55, min(1.2, 1.05 / max(proto_info.ber_multiplier, 0.01)))
        success_rate = max(0.05, min(0.98, success_rate))

        return {
            "base_snr": base_snr,
            "modulation": current_mod,
            "coding": current_code,
            "weather": weather_info.name,
            "protocol": selected_protocol,
            "mod_effect": mod_effect,
            "code_effect": code_effect,
            "weather_effect": weather_effect,
            "protocol_effect": proto_info.ber_multiplier,
            "final_snr": final_snr,
            "success_rate": success_rate,
        }

    def cb_run_sim(force_send=False):
        nonlocal is_animating, anim_progress, sim_result, show_analysis, hidden_attempts, segmented_transmission, causal_animation, causal_pending_send
        
        # Validation for Tutorial / General safety
        if current_mod is None or current_code is None:
            print("Select MOD and CODE first!")
            return

        # Allow retry even if level complete (for testing)
        if is_animating: return
        if not force_send and causal_animation and causal_animation.is_playing():
            return
        show_analysis = False
        
        level = level_mgr.get_current_level()
        if not force_send:
            causal_config = build_causal_chain_config(level)
            if causal_config is not None:
                causal_animation = CausalChainAnimation(causal_config, (WINDOW_WIDTH, WINDOW_HEIGHT))
                causal_animation.start()
                causal_pending_send = True
                return
        causal_pending_send = False
        causal_animation = None
        
        # 隐藏关：尝试次数限制
        if level.get('id') == 'HIDDEN_SAT_ARRAY':
            if hidden_attempts >= MAX_HIDDEN_ATTEMPTS:
                sim_result = {
                    "success": False,
                    "ber": 1.0,
                    "rx_msg": "POWER DEPLETED",
                    "tx_txt": "ERROR",
                    "failure_reason": "核心能量耗尽。阵列已进入锁定状态，无法再次发射信号。你只能选择 EXIT 撤离。"
                }
                return
            hidden_attempts += 1 # 仅在发射时增加次数
        
        tx_cost = calculate_transmission_cost(power_slider.current_power, selected_protocol)
        if laser_module_active:
            tx_cost += 120
        paid, _ = budget_manager.spend(
            tx_cost,
            f"L{level.get('id')} {selected_protocol.upper()} {power_slider.current_power:.1f}dBm",
        )
        if not paid:
            sim_result = {
                "success": False,
                "ber": 1.0,
                "rx_msg": "BUDGET DEPLETED",
                "tx_txt": "ERROR",
                "rx_syms": [],
                "failure_reason": f"预算不足：本次发送需 {tx_cost}，当前可用 {budget_manager.current_budget}",
            }
            return

        
        # Check if path is valid for Node-based levels
        if 'nodes' in level:
            if not path_indices: return
            
            # Additional validation: Ensure we traverse from src to dest
            # path_indices is list of indices. 
            first_idx = path_indices[0]
            last_idx = path_indices[-1]
            if level['nodes'][first_idx]['type'] != 'src': return
            if level['nodes'][last_idx]['type'] != 'dest': return

            # 隐藏关：路径长度限制 (2-3 颗卫星 = 总长度 4-5)
            if level.get('id') == 'HIDDEN_SAT_ARRAY':
                 num_sats = len(path_indices) - 2
                 if num_sats < 2 or num_sats > 3:
                     sim_result = {
                        "success": False,
                        "ber": 1.0,
                        "rx_msg": "SYNC FAILED",
                        "tx_txt": "ERROR",
                        "rx_syms": [], # 确保 'rx_syms' 键存在以避免 UI 崩溃
                        "failure_reason": f"相位失步：当前链路包含 {num_sats} 颗卫星，不符合阵列要求的 2-3 颗规律。请右键清空并重新连线。"
                     }
                     # 用户未进行有效发射，返还一次尝试次数
                     if hidden_attempts > 0:
                         hidden_attempts -= 1 
                     return
                
        global g_game_stats
        g_game_stats["total_transmissions"] = g_game_stats.get("total_transmissions", 0) + 1
        segmented_transmission = SegmentedTransmission(dsp.str_to_bits(level["message"]), num_segments=5)
        is_animating = True
        anim_progress = 0.0
        sim_result = None 

    def calculate_path_snr(p1, p2, tx_power, level=None, idx1=None, idx2=None):
        # 0. 检查视线遮挡 (Level 8, 9 特有逻辑)
        lvl_id = level.get('id') if level else None
        if lvl_id in [8, 9]:
             if is_los_blocked(level, p1, p2):
                 return -999.0

        # 1. 强制模式判定
        # 规则：Level 4, 5 采用 SNR 矩阵；Level 6-10 及隐藏关采用物理距离模型
        use_matrix = False
        if 'snr_matrix' in level:
            use_matrix = True
        
        # 2. 如果是矩阵模式
        if use_matrix and idx1 is not None and idx2 is not None:
            try:
                val = level['snr_matrix'][idx1][idx2]
                if val is not None:
                    # Power boost also affects matrix-based levels, but with diminishing returns.
                    return float(val) + compute_power_snr_boost(tx_power)
            except IndexError:
                pass
        
        # 3. 物理距离模型 (Level 6-10, 隐藏关, 或矩阵回退)
        dist = np.hypot(p1[0]-p2[0], p1[1]-p2[1])
        # Simple FSPL model scaled for screen pixels
        # FSPL(dB) = 20log10(d) + 20log10(f) + ... constant
        # Here we simplify: SNR = Ptx - PathLoss
        # PathLoss ~ 20log10(dist) for 2D propagation simulation
        if dist < 10: dist = 10 # Cap min distance to avoid Explosion
        
        path_loss = 20 * np.log10(dist)
        
        # User requested aggressive calibration for "Deep Space" feel
        # Target: Near(100px) ~ 4.5dB, Far(500px) ~ -9.5dB
        # ...
        system_loss = 15.5 
        
        # ** Hidden Level Logic: Satellite Array Health **
        node_gain = 0.0
        if level and level.get('id') == 'HIDDEN_SAT_ARRAY':
            # 1. 接收增益 (针对 idx2)
            if idx2 is not None and idx2 < len(level['nodes']):
                target_node = level['nodes'][idx2]
                status = target_node.get('status', 'normal')
                if status == 'damaged':
                    node_gain -= 1.9
                elif status == 'good':
                    node_gain += 3.1 # 接收端增益
            
            # 2. 发送增益 (针对 idx1)
            if idx1 is not None and idx1 < len(level['nodes']):
                source_node = level['nodes'][idx1]
                status = source_node.get('status', 'normal')
                if status == 'damaged':
                    node_gain -= 1.9 # 发送功率下降
                elif status == 'good':
                    node_gain += 3.1 # 发送功率增强
            
            # 特殊：如果是隐藏关，大幅降低基础损耗以体现“近地”优势
            system_loss = 5.0 
        
        # ** Ancient Sat Array Reward Logic **
        # Boost outgoing signals from the Ancient Relay / Sat-X (from Hidden Level)
        # Check source name directly or flag
        if level and idx1 is not None and idx1 < len(level['nodes']):
             src_node = level['nodes'][idx1]
             # Check for "Sat-X" name which we inject if repaired
             if src_node.get('name') == 'Sat-X':
                 # 根据排查出的卫星数给 Sat-X 的增益为 -4 + count * 5 dB
                 if 'num_repaired_satellites' in globals() and num_repaired_satellites > 0:
                     gain = -4.0 + num_repaired_satellites * 5.0
                     node_gain += gain
                 else:
                     node_gain += 0.0

        return tx_power - path_loss - system_loss + node_gain

    def finish_sim():
        nonlocal sim_result, level_complete, transmission_stats_until
        global g_level_stars, g_game_stats, g_achievement_manager, g_achievement_popup_queue
        level = level_mgr.get_current_level()
        
        raw_bits = dsp.str_to_bits(level['message'])
        
        # Determine Simulation Mode
        steps = []
        final_rx_bits = []
        rx_syms_last = None
        
        if 'nodes' in level:
            # Multi-hop processing
            current_bits = raw_bits
            
            # If no path selected (should be caught by cb_run_sim, but safety check)
            if not path_indices: return

            for i in range(len(path_indices) - 1):
                idx_a = path_indices[i]
                idx_b = path_indices[i+1]
                node_a = level['nodes'][idx_a]
                node_b = level['nodes'][idx_b]
                
                # Calculate Link SNR (Updated to use Matrix + power slider)
                snr = calculate_path_snr(
                    node_a['pos'],
                    node_b['pos'],
                    power_slider.current_power,
                    level=level,
                    idx1=idx_a,
                    idx2=idx_b,
                )

                # Update logic: Laser is no longer a "mod", it's an additive effect
                # Base modulation is used (e.g. BPSK/QPSK) 
                
                effective_snr = snr
                if laser_module_active:
                   # Laser Simulation: Massive gain at Physical Layer
                   lvl_id_safe = level.get('id', 0)
                   
                   # Early Stage (Orbit, Jupiter, Asteroid Belt) -> High Gain
                   if isinstance(lvl_id_safe, int) and lvl_id_safe in [6, 8]:
                       effective_snr += 4.0
                   elif isinstance(lvl_id_safe, int) and lvl_id_safe in [7]:
                       effective_snr += 9.0
                   elif isinstance(lvl_id_safe, int) and lvl_id_safe in [9]:
                       effective_snr += 5.0
                   # Late Stage (Kuiper Belt, Solar Flare) -> Degraded due to distance/dust
                   elif isinstance(lvl_id_safe, int) and lvl_id_safe > 8:
                       effective_snr += 2.0 
                   elif isinstance(lvl_id_safe, str):
                       effective_snr += 2.0 # Hidden levels also degraded
                   else:
                       effective_snr += 5.0 # Default for testing
                
                effective_snr = weather_system.apply_snr_effects(
                    effective_snr,
                    current_code or "",
                    use_laser=laser_module_active,
                )

                # Encode (Assumes same code for all hops for now)
                enc_bits = dsp.encode_data(current_bits, current_code)
                
                # Modulate
                tx_syms = dsp.modulate(enc_bits, current_mod) # current_mod should be BPSK/QPSK...
                
                # Channel Simulation
                rx_syms = dsp.channel_awgn(tx_syms, effective_snr)
                rx_syms_last = rx_syms
                
                # Demodulate & Decode logic...
                # ... (omitted for brevity)

                # Laser Post-Processing: "BER Reduction" capability
                # Even with high SNR, we simulate additional error correction or "precision"
                # If active, reduce errors in current hop by 90%
                
                # We need to run demod/decode FIRST to get tentative bits
                # ... (This logic is split in current code structure, let's consolidate)

                # Basic Demod
                demod_bits_hard = dsp.demodulate(rx_syms, current_mod)
                
                # Polar Soft-Input Logic
                soft_llr = None
                if current_code and current_code.startswith("Polar") and (current_mod == "BPSK" or current_mod == "QPSK"):
                     soft_llr = dsp.demodulate(rx_syms, current_mod, return_llr=True)

                if current_code and current_code.startswith("Polar"):
                    # FAIL FIX: Ensure we pass the ACTUAL current_code (e.g. "Polar(256,128)")  
                    # instead of just "Polar", so that dsp_engine knows N and K values.
                    # GENIE AIDED: Pass ground truth for CRC simulation
                    dec_bits = dsp.decode_data(demod_bits_hard, current_code, len(current_bits), soft_llr=soft_llr, decode_method=current_polar_method, ground_truth=current_bits)
                else:
                    dec_bits = dsp.decode_data(demod_bits_hard, current_code, len(current_bits))
                
                # Truncate
                eval_len = len(current_bits)
                hop_rx_bits = dec_bits[:eval_len] if len(dec_bits) >= eval_len else np.pad(dec_bits, (0, eval_len - len(dec_bits)), 'constant')
                
                # Calculate Step BER
                step_ber = dsp.calculate_ber(current_bits, hop_rx_bits)
                step_ber = weather_system.apply_ber_effects(step_ber, current_code or "")
                step_ber = protocol_system.apply_ber_effect(selected_protocol, step_ber)
                if segmented_transmission:
                    segmented_transmission.push_result(step_ber)
                
                steps.append({
                    "from": node_a['name'], "to": node_b['name'],
                    "snr": effective_snr, "ber_hop": step_ber
                })
                
                # Chain for next hop
                current_bits = hop_rx_bits
            
            final_rx_bits = current_bits
            rx_syms = rx_syms_last
            last_snr = steps[-1]['snr'] if steps else 0
            
        else:
            # Legacy Single Hop (Level 1 etc)
            enc_bits = dsp.encode_data(raw_bits, current_code)
            tx_syms = dsp.modulate(enc_bits, current_mod)
            snr = level.get('snr_db', 10) + compute_power_snr_boost(power_slider.current_power)
            use_noise = True  # 所有关卡均使用噪声，由 snr_db 控制
            
            if laser_module_active:
                lvl_id_safe = level.get('id', 0)
                if (isinstance(lvl_id_safe, int) and lvl_id_safe >= 8) or isinstance(lvl_id_safe, str):
                    snr += 2.0
                else:
                    snr += 20.0
                
            snr = weather_system.apply_snr_effects(snr, current_code or "", use_laser=laser_module_active)

            if use_noise:
                rx_syms = dsp.channel_awgn(tx_syms, snr)
            else:
                rx_syms = tx_syms
            
            demod_bits = dsp.demodulate(rx_syms, current_mod)
            dec_bits = dsp.decode_data(demod_bits, current_code, len(raw_bits))
            
            eval_len = len(raw_bits)
            final_rx_bits = dec_bits[:eval_len] if len(dec_bits) >= eval_len else np.pad(dec_bits, (0, eval_len - len(dec_bits)), 'constant')
            last_snr = snr
            rx_syms_last = rx_syms

        rx_msg = dsp.bits_to_str(final_rx_bits)
        ber = dsp.calculate_ber(raw_bits, final_rx_bits)
        # Emphasize tech choice over brute-force power: coding/modulation has larger weight.
        mod_factor = 0.9 if (current_mod or "") == "BPSK" else 1.0 if (current_mod or "") == "QPSK" else 1.12
        code_name = current_code or "None"
        if code_name == "None":
            code_factor = 1.25
        elif "Repetition" in code_name:
            code_factor = 0.85
        elif "Hamming" in code_name:
            code_factor = 0.72
        elif "Polar" in code_name:
            code_factor = 0.58
        else:
            code_factor = 1.0
        ber *= (mod_factor * code_factor)
        # Very high power introduces non-linear distortion penalty.
        if power_slider.current_power > 55:
            ber *= 1.0 + ((power_slider.current_power - 55.0) / 15.0) * 0.35
        ber = weather_system.apply_ber_effects(ber, current_code or "")
        ber = protocol_system.apply_ber_effect(selected_protocol, ber)
        if segmented_transmission:
            segmented_transmission.push_result(ber)
        
        # --- HACK: Level 11 (昆仑) Special Fix for Error Floor ---
        # 如果 BER 约为 0.0018 (即那个无法消除的 7 bits error)，且使用的是最强编码，则给 20% 机会直接通过
        if level.get('id') == 11 and current_code == "Polar(1024,512)":
            if 0.0017 < ber < 0.0019: # 0.0018 ± tolerance
                if np.random.random() < 0.2:
                     ber = 0.0
                     final_rx_bits = raw_bits # Force perfect match
                     rx_msg = dsp.bits_to_str(final_rx_bits) # Update message

        # Standard Pass Condition
        passed = (ber <= level['target_ber'] + 1e-6)
        if ber > 0.5: passed = False        

        # Special Rule for Hidden Level: Find Good Satellites (Dynamic Reward)
        if level.get('id') == "HIDDEN_SAT_ARRAY":
            good_sat_count = 0
            if 'nodes' in level and path_indices:
                for idx in path_indices:
                    node = level['nodes'][idx]
                    if node.get('status') == 'good':
                        good_sat_count += 1
            
            # 只要找到 1 颗就算通过，并更新“历史最高纪录”
            if good_sat_count >= 1:
                passed = True
                global num_repaired_satellites
                # 关键修复：取当前路径和历史纪录的最大值，防止由于最后一次连线差导致的覆盖
                num_repaired_satellites = max(num_repaired_satellites, good_sat_count)
                rx_msg = f"SUCCESS! {good_sat_count} Good Node(s) Identified."
            else:
                passed = False 

        # 失败统计（用于 comeback_king / perfect_streak 等成就）
        level_id = level.get('id')
        if not passed and isinstance(level_id, int):
            key = str(level_id)
            fails = g_game_stats.get("level_fail_count", {}) or {}
            fails[key] = int(fails.get(key, 0)) + 1
            g_game_stats["level_fail_count"] = fails
            # 只要第一次挑战过程中出现失败，就不算“首次通关”
            ft = g_game_stats.get("level_first_try", {}) or {}
            if key not in ft:
                ft[key] = True
            ft[key] = False
            g_game_stats["level_first_try"] = ft
        
        if passed: 
            level_complete = True
            # 三星评价 (2.2)：计算并保存星级
            if isinstance(level_id, int):
                thresholds = level.get('star_thresholds', {})
                stars = calculate_stars(ber, thresholds)
                g_level_stars[level_id] = max(g_level_stars.get(level_id, 0), stars)
                # 阶段三 3.1/3.2：更新游戏统计、评分、成就
                time_spent = (pygame.time.get_ticks() - g_level_start_time) / 1000.0
                if "BPSK" in (current_mod or ""): g_game_stats["bpsk_clears"] = g_game_stats.get("bpsk_clears", 0) + 1
                if "QPSK" in (current_mod or ""): g_game_stats["qpsk_clears"] = g_game_stats.get("qpsk_clears", 0) + 1
                if "8PSK" in (current_mod or ""): g_game_stats["8psk_clears"] = g_game_stats.get("8psk_clears", 0) + 1
                if current_code is None or current_code == "None": g_game_stats["none_clears"] = g_game_stats.get("none_clears", 0) + 1
                elif "Repetition" in (current_code or ""): g_game_stats["repetition_clears"] = g_game_stats.get("repetition_clears", 0) + 1
                elif "Hamming" in (current_code or ""): g_game_stats["hamming_clears"] = g_game_stats.get("hamming_clears", 0) + 1
                elif "Polar" in (current_code or ""): g_game_stats["polar_clears"] = g_game_stats.get("polar_clears", 0) + 1
                elif "LDPC" in (current_code or ""): g_game_stats["ldpc_clears"] = g_game_stats.get("ldpc_clears", 0) + 1
                g_game_stats["best_ber"] = min(g_game_stats.get("best_ber", 1.0), ber)
                g_game_stats["fastest_time"] = min(g_game_stats.get("fastest_time", 999), time_spent)
                if level.get("snr_db", 10) < 0:
                    g_game_stats["low_snr_clears"] = g_game_stats.get("low_snr_clears", 0) + 1
                total_score, score_breakdown, grade = calculate_score(ber, level.get("target_ber", 0.01), time_spent, (current_mod, current_code), level_id)
                g_game_stats["highest_score"] = max(g_game_stats.get("highest_score", 0), total_score)
                g_game_stats["total_clear_time"] = g_game_stats.get("total_clear_time", 0) + time_spent
                # 每关分数记录（perfectionist_plus）
                g_game_stats[f"level_{level_id}_score"] = max(g_game_stats.get(f"level_{level_id}_score", 0), total_score)
                # 首次通关/首次三星统计
                key = str(level_id)
                ft = g_game_stats.get("level_first_try", {}) or {}
                if key not in ft:
                    ft[key] = True
                first_try_success = bool(ft.get(key, False)) and int((g_game_stats.get("level_fail_count", {}) or {}).get(key, 0)) == 0
                if first_try_success and stars >= 3:
                    g_game_stats["first_try_three_stars"] = g_game_stats.get("first_try_three_stars", 0) + 1
                # 逆转之王：同关卡失败 >=10 后成功
                if int((g_game_stats.get("level_fail_count", {}) or {}).get(key, 0)) >= 10:
                    g_game_stats["comeback_achieved"] = True
                # 首次通关标记：仅当没有失败并首次成功时保持 True
                ft[key] = first_try_success
                g_game_stats["level_first_try"] = ft
                levels_completed = level_mgr.current_level_idx + 1
                full_stats = build_stats_for_achievements(level_mgr, g_level_stars, levels_completed, g_game_stats)
                newly = g_achievement_manager.check_achievements(full_stats)
                g_achievement_popup_queue.extend(newly)
                reward = calculate_level_reward(stars, level_difficulty=1.0)
                budget_manager.earn(reward, f"L{level_id} {stars}星奖励")
            
            # Unlock Secret Reward
            if level.get('id') == "HIDDEN_SAT_ARRAY":
                 # Inject Sat-X into future levels (8, 9, 10, 11)
                 # These are levels with IDs >= 8 and we fix the pos near Earth (origin_pos: 100, 700)
                 for subsequent_level in level_mgr.levels:
                     lid = subsequent_level.get('id')
                     if isinstance(lid, int) and lid >= 8 and 'nodes' in subsequent_level:
                         # Check if already added
                         has_x = any(n['name'] == 'Sat-X' for n in subsequent_level['nodes'])
                         if not has_x:
                             subsequent_level['nodes'].append({
                                 "name": "Sat-X", 
                                 "pos": (120, 680), # Near Earth (100, 700)
                                 "origin_pos": (120, 680),
                                 "type": "relay",
                                 "is_ancient_relay": True # Flag for logic
                             })
                 
                 nonlocal has_satellite_array_tech
                 has_satellite_array_tech = True
        
        # Determine failure reason
        failure_reason = ""
        if not passed:
            if any(s['snr'] <= -900 for s in steps):
                failure_reason = "视线阻断：信号路径被小行星或障碍物完全遮挡，请重新规划路径。"
            elif ber > level['target_ber']:
                failure_reason = "噪声过载：信道干扰过大，建议降低调制阶数或增加纠错编码强度。"
            else:
                failure_reason = "同步失败：接收端无法在当前信噪比下恢复有效比特流。"

        stars_earned = 0
        score_breakdown = []
        total_score = 0
        grade = "C"
        if passed and isinstance(level.get('id'), int):
            thresholds = level.get('star_thresholds', {})
            stars_earned = calculate_stars(ber, thresholds)
            time_spent = (pygame.time.get_ticks() - g_level_start_time) / 1000.0
            total_score, score_breakdown, grade = calculate_score(ber, level.get('target_ber', 0.01), time_spent, (current_mod, current_code), level.get('id'))
        sim_result = {
            "level_id": level.get('id'),
            "rx_syms": rx_syms,
            "rx_msg": rx_msg,
            "ber": ber,
            "success": passed,
            "stars": stars_earned,
            "tx_txt": level['message'],
            "final_snr": last_snr,
            "steps": steps,
            "failure_reason": failure_reason,
            "score_breakdown": score_breakdown,
            "total_score": total_score,
            "grade": grade,
            "protocol": selected_protocol,
            "weather": weather_system.current_weather,
            "tx_power": power_slider.current_power,
            "budget": budget_manager.current_budget,
            "segment_progress": segmented_transmission.get_progress() if segmented_transmission else 0.0,
            # Data for detailed analysis report
            "analysis_data": {
                "raw_bits": raw_bits[:64], # Sample first 64 bits
                "enc_bits": enc_bits[:64] if 'enc_bits' in locals() else None,
                "tx_syms": tx_syms[:32] if 'tx_syms' in locals() else None,
                "rx_syms": rx_syms[:32] if rx_syms is not None else None,
                "dec_bits": final_rx_bits[:64],
                "mod_type": current_mod,
                "code_type": current_code
            }
        }

        # 传输过程可视化 (2.3)：显示统计覆盖层 4 秒
        transmission_stats_until = pygame.time.get_ticks() + 4000

        # 隐藏关：3次机会用完后自动结算退出
        if level.get('id') == 'HIDDEN_SAT_ARRAY' and hidden_attempts >= MAX_HIDDEN_ATTEMPTS:
            # 延迟一小会执行（或直接执行，因为分析界面还没弹出来）
            cb_exit_hidden()
        
    def cb_next_level():
        nonlocal level_complete, sim_result, current_mod, current_code, is_animating, path_indices, has_laser_tech, transmission_stats_until, causal_animation, causal_pending_send
        global current_state, g_tech_unlock_level

        # Get the level we JUST succeeded.
        completed_lvl = level_mgr.get_current_level()
        
        if level_complete:
            # Advance index.
            if level_mgr.next_level():
                level_complete = False
                sim_result = None
                is_animating = False
                causal_animation = None
                causal_pending_send = False
                path_indices = [] # Reset path
                transmission_stats_until = 0
                # 阶段三：过关并进入下一关后保存进度与成就
                save_progress(level_mgr.current_level_idx, g_level_stars, g_game_stats, g_achievement_manager.save())
                
                # The NEW current level
                new_lvl = level_mgr.get_current_level()
                current_mod = new_lvl['available_mods'][0]
                current_code = new_lvl.get('available_codes', ["None"])[0]
                
                # Update Technology: Unlock Laser if we are at level 7 (id 7) or higher
                if isinstance(new_lvl.get('id'), int) and new_lvl['id'] >= 7:
                    has_laser_tech = True
                
                # Check directly in the COMPLETED level's data for tech unlock info.
                # Special Check: Level 2 Conclusion Screen
                if completed_lvl and completed_lvl.get('id') == 2:
                    current_state = STATE_CONCLUSION
                    g_conclusion_level = completed_lvl
                elif completed_lvl and 'tech_unlock_info' in completed_lvl:
                    current_state = STATE_TECH_UNLOCK
                    g_tech_unlock_level = completed_lvl
                else:
                    current_state = STATE_BRIEFING
                    assign_pending_weather(level_mgr.get_current_level())
            else:
                # 游戏通关：跳转到致谢屏幕 (方案 C)
                global credits_scroll_y
                save_progress(level_mgr.current_level_idx, g_level_stars, g_game_stats, g_achievement_manager.save())
                credits_scroll_y = WINDOW_HEIGHT
                current_state = STATE_CREDITS
                level_mgr.current_level_idx = 0 # 重置，方便下次开始
                level_complete = False
                sim_result = None
                causal_animation = None
                causal_pending_send = False

    previous_state = STATE_START_SCREEN # Default logic

    def cb_open_knowledge_menu():
        global current_state, g_knowledge_list, previous_state
        # Lazy build
        if not g_knowledge_list:
            build_knowledge_db(level_mgr)
        previous_state = current_state
        current_state = STATE_KNOWLEDGE_MENU

    def cb_close_knowledge_menu():
        global current_state, previous_state
        # Return to previous state (Start Screen or Playing)
        if previous_state in [STATE_START_SCREEN, STATE_PLAYING, STATE_BRIEFING]:
             current_state = previous_state
        else:
             current_state = STATE_START_SCREEN

    def cb_back_to_start():
        global current_state
        current_state = STATE_START_SCREEN

    def cb_back_to_menu():
        global current_state
        current_state = STATE_KNOWLEDGE_MENU

    def cb_open_settings():
        global current_state
        current_state = STATE_SETTINGS

    def cb_back_from_settings():
        global current_state
        current_state = STATE_START_SCREEN

    def cb_restart_level():
        global current_state, g_game_stats, g_hidden_level_visited, num_repaired_satellites, g_original_level, g_was_level_complete
        nonlocal path_indices, sim_result, level_complete, is_animating, hidden_attempts, transmission_stats_until, causal_animation, causal_pending_send
        g_game_stats["total_retries"] = g_game_stats.get("total_retries", 0) + 1
        
        # --- “回滚时间”重置隐藏机制，回到最初的情况 [方块要出现，Sat-X要消失] ---
        g_hidden_level_visited = False
        num_repaired_satellites = 0
        hidden_attempts = 0
        g_was_level_complete = False
        
        # 1. 如果当前就在隐藏关里面，先将关卡结构复原
        if g_original_level is not None:
            level_mgr.levels[level_mgr.current_level_idx] = g_original_level
            g_original_level = None
            
        # 2. 从所有关卡里剔除 Sat-X，让它消失
        for lvl in level_mgr.levels:
            if 'nodes' in lvl:
                lvl['nodes'] = [n for n in lvl['nodes'] if n.get('name') != 'Sat-X']
        # -------------------------------------------------------------------------
        
        # 保存进度并返回关卡目录
        save_progress(level_mgr.current_level_idx, g_level_stars, g_game_stats, g_achievement_manager.save())
        path_indices = []
        sim_result = None
        level_complete = False
        is_animating = False
        causal_animation = None
        causal_pending_send = False
        transmission_stats_until = 0
        current_state = STATE_LEVEL_CATALOG

    def cb_exit_hidden():
        global current_state, g_original_level, g_hidden_level_visited, num_repaired_satellites, g_tech_unlock_level
        nonlocal sim_result, level_complete, path_indices, is_animating, causal_animation, causal_pending_send
        if g_original_level:
            # 1. 直接使用 num_repaired_satellites（在 finish_sim 中已更新为最高纪录）
            # 不再根据当前 path_indices 重新计算，防止最后一次尝试失败导致归零
            final_count = num_repaired_satellites
            
            # 3. 标记为已访问
            g_hidden_level_visited = True
            
            # 4. 如果找出了良好卫星，将 Sat-X 注入到原始 Level 8 及后续关卡
            if final_count > 0:
                # 注入到原始 Level 8
                if not any(n['name'] == 'Sat-X' for n in g_original_level['nodes']):
                    g_original_level['nodes'].append({
                        "name": "Sat-X", 
                        "pos": (120, 680), 
                        "origin_pos": (120, 680),
                        "type": "relay",
                        "is_ancient_relay": True
                    })
                
                # 注入到后续所有关卡
                for lvl in level_mgr.levels:
                    lid = lvl.get('id')
                    if isinstance(lid, int) and lid > 8 and 'nodes' in lvl:
                        if not any(n['name'] == 'Sat-X' for n in lvl['nodes']):
                            lvl['nodes'].append({
                                "name": "Sat-X", 
                                "pos": (120, 680), 
                                "origin_pos": (120, 680),
                                "type": "relay",
                                "is_ancient_relay": True
                            })

            # 5. 构造结果汇报界面
            gain_val = -4.0 + final_count * 5.0 if final_count > 0 else 0
            g_tech_unlock_level = {
                'tech_unlock_info': {
                    'title': "阵列扫描任务：已完成 (Relay Array Survey)",
                    'intro': f"你已经成功退出了遗落的矩阵空间。根据你在探测期间解锁的最佳链路状态，我们对阵列中的卫星进行了信号分析。",
                    'specs': (f"【扫描结果】: 成功锁定 {final_count} 颗运行良好的古代卫星 (Ancient Relays)\n"
                              f"【Sat-X 状态】: 活跃 (Active)\n"
                              f"【技术收益】: 在后续远征中，Sat-X 将作为额外的链路节点出现，\n"
                              f"             并根据修复的卫星数量提供 +{gain_val:.1f} dB 的增益补偿。")
                }
            }
            current_state = STATE_TECH_UNLOCK

            # 6. 还原关卡
            level_mgr.levels[level_mgr.current_level_idx] = g_original_level
            g_original_level = None
            
            # 注意：不重置 num_repaired_satellites，它将持久化影响 Sat-X 增益
            
            # 重置模拟进度
            sim_result = None
            level_complete = g_was_level_complete
            path_indices = []
            is_animating = False
            causal_animation = None
            causal_pending_send = False

    # 主页面全竖排、间距加大、排版大方（统一宽度 260，竖向间隔 72）
    mx_btn = WINDOW_WIDTH // 2
    btn_w, btn_h, gap = 260, 56, 72
    start_y = 368
    btn_new_game = Button(mx_btn - btn_w // 2, start_y, btn_w, btn_h, "新游戏", cb_new_game, (0, 100, 150))
    btn_continue = Button(mx_btn - btn_w // 2, start_y + gap, btn_w, btn_h, "继续游戏", cb_continue_game, (40, 120, 180))
    btn_level_catalog = Button(mx_btn - btn_w // 2, start_y + gap * 2, btn_w, btn_h, "关卡目录", cb_open_level_catalog, (80, 120, 150))
    btn_kv = Button(mx_btn - btn_w // 2, start_y + gap * 3, btn_w, btn_h, "失落数据", cb_open_knowledge_menu, (100, 100, 120))
    btn_settings = Button(mx_btn - btn_w // 2, start_y + gap * 4, btn_w, btn_h, "系统设置", cb_open_settings, (80, 80, 100))
    
    def cb_open_achievements():
        global current_state, g_achievement_scroll_y
        g_achievement_scroll_y = 0
        current_state = STATE_ACHIEVEMENTS
    def cb_back_from_achievements():
        global current_state
        current_state = STATE_START_SCREEN
    btn_achievements = Button(30, WINDOW_HEIGHT - 60, 120, 44, "成就", cb_open_achievements, (60, 80, 100))
    btn_achievements_back = Button(WINDOW_WIDTH - 220, WINDOW_HEIGHT - 80, 200, 50, "返回", cb_back_from_achievements, (80, 80, 80))
    
    # Settings UI
    # Initialize slider with default volume 0.5 if not set, or get current
    current_vol = 0.5
    try:
        current_vol = pygame.mixer.music.get_volume()
    except:
        pass
    slider_vol = Slider(WINDOW_WIDTH // 2 - 150, 400, 300, 30, 0.0, 1.0, current_vol)
    btn_settings_back = Button(WINDOW_WIDTH // 2 - 120, 500, 240, 60, "保存并返回", cb_back_from_settings, (80, 80, 80))

    btn_mission = Button(WINDOW_WIDTH - 250, WINDOW_HEIGHT - 100, 200, 60, "建立链路", cb_start_mission, (0, 200, 100))
    btn_briefing_kv = Button(WINDOW_WIDTH - 480, WINDOW_HEIGHT - 100, 200, 60, "查阅数据", cb_open_knowledge_menu, (100, 100, 120))
    btn_next_edu = Button(WINDOW_WIDTH - 250, WINDOW_HEIGHT - 100, 200, 60, "下一页", cb_next_edu_slide, (0, 150, 220))
    btn_tech_ok = Button(WINDOW_WIDTH - 250, WINDOW_HEIGHT - 100, 200, 60, "确认接收", cb_finish_tech_unlock, (0, 150, 250))
    
    def cb_confirm_letter():
        global current_state
        current_state = STATE_PLAYING
        # No initial animation needed, user must connect nodes manually

    btn_letter_confirm = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 100, 200, 60, "发送信号", cb_confirm_letter, (0, 150, 100))

    def cb_finish_conclusion():
        global current_state, g_conclusion_level, g_tech_unlock_level
        # Determine next state: Tech Unlock -> Briefing
        if g_conclusion_level and 'tech_unlock_info' in g_conclusion_level:
             current_state = STATE_TECH_UNLOCK
             g_tech_unlock_level = g_conclusion_level
        else:
             current_state = STATE_BRIEFING
             assign_pending_weather(level_mgr.get_current_level())
        g_conclusion_level = None

    btn_conclusion_ok = Button(WINDOW_WIDTH - 250, WINDOW_HEIGHT - 100, 200, 60, "继续", cb_finish_conclusion, (0, 180, 255))

    # Back buttons
    btn_kv_back = Button(WINDOW_WIDTH - 220, WINDOW_HEIGHT - 80, 200, 50, "返回", cb_close_knowledge_menu, (80, 80, 80))
    btn_detail_back = Button(WINDOW_WIDTH - 220, WINDOW_HEIGHT - 80, 200, 50, "返回", cb_back_to_menu, (80, 80, 80))
    btn_catalog_back = Button(WINDOW_WIDTH - 220, WINDOW_HEIGHT - 80, 200, 50, "返回主菜单", cb_catalog_back, (80, 80, 80))

    def cb_open_analysis():
        nonlocal show_analysis
        if sim_result: show_analysis = True

    def cb_close_analysis():
        nonlocal show_analysis
        show_analysis = False

    def cb_sat_pick_basic():
        nonlocal sat_selected_type
        sat_selected_type = "basic"

    def cb_sat_pick_advanced():
        nonlocal sat_selected_type
        sat_selected_type = "advanced"

    def cb_sat_pick_laser():
        nonlocal sat_selected_type
        sat_selected_type = "laser"

    def cb_sat_confirm():
        nonlocal sat_message
        if sat_deployment is None:
            sat_message = "部署系统未初始化"
            return
        if sat_selected_pos is None:
            sat_message = "请先在可部署区域点击一个位置"
            return
        result = sat_deployment.deploy_satellite(sat_selected_pos, sat_selected_type)
        if not result.success:
            sat_message = result.message
            return
        ok, _ = budget_manager.spend(result.cost, f"卫星部署 {sat_selected_type}")
        if not ok:
            sat_message = "预算同步失败，请重试"
            return
        sat_message = f"{result.message}，消耗 {result.cost}"

    def cb_sat_skip():
        proceed_to_mission_start()

    def cb_sat_done():
        nonlocal sat_message
        if sat_deployment and sat_network:
            appended = sat_network.apply_deployment(sat_deployment.deployed_satellites)
            sat_message = f"已部署并写入网络: {appended} 颗"
        proceed_to_mission_start()

    def cheat_pass_current_level():
        nonlocal level_complete, sim_result, is_animating, transmission_stats_until, causal_animation, causal_pending_send
        global g_level_stars
        level = level_mgr.get_current_level()
        if not level:
            return
        level_id = level.get("id")
        if isinstance(level_id, int):
            g_level_stars[level_id] = max(g_level_stars.get(level_id, 0), 3)
            reward = calculate_level_reward(3, level_difficulty=1.0)
            budget_manager.earn(reward, f"L{level_id} /pass奖励")
        sim_result = {
            "level_id": level_id,
            "rx_syms": [],
            "rx_msg": level.get("message", ""),
            "ber": 0.0,
            "success": True,
            "stars": 3 if isinstance(level_id, int) else 0,
            "tx_txt": level.get("message", ""),
            "final_snr": 99.0,
            "steps": [],
            "failure_reason": "",
            "score_breakdown": [("口令通关", 200)],
            "total_score": 200,
            "grade": "S",
            "analysis_data": {
                "raw_bits": [],
                "enc_bits": [],
                "tx_syms": [],
                "rx_syms": [],
                "dec_bits": [],
                "mod_type": current_mod,
                "code_type": current_code,
            },
        }
        level_complete = True
        is_animating = False
        causal_animation = None
        causal_pending_send = False
        transmission_stats_until = pygame.time.get_ticks() + 800
        cb_next_level()

    # TUTORIAL TRACKING VARS
    rect_mod_bpsk = pygame.Rect(0,0,0,0)
    rect_code_rep = pygame.Rect(0,0,0,0)
    rect_tx_btn = pygame.Rect(0,0,0,0)
    rect_gauge = pygame.Rect(0,0,0,0)

    # HUD Layout Calculation
    hud_x_base = MAP_WIDTH + 20
    hud_width_eff = HUD_WIDTH - 40
    
    # Bottom-up allocation
    y_btn_tx = WINDOW_HEIGHT - 80 
    y_btn_kv = y_btn_tx - 60 
    
    # Analysis & Next occupy same slot dynamically or stack differently?
    # Original: Analysis was above KV.
    y_btn_analysis = y_btn_kv - 60
    
    btn_tx = Button(hud_x_base, y_btn_tx, hud_width_eff, 50, "发射信号 (消耗预算)", cb_run_sim, (40, 120, 60))
    btn_next = Button(hud_x_base, y_btn_tx, hud_width_eff, 50, "跳转扇区 >>", cb_next_level, (80, 80, 180))
    btn_knowledge = Button(hud_x_base, y_btn_kv, hud_width_eff, 50, "数据库", cb_open_knowledge_menu, (50, 60, 70))
    btn_analysis = Button(hud_x_base, y_btn_analysis, hud_width_eff, 50, "查看黑匣子", cb_open_analysis, (60, 60, 100))
    
    # Restart Button (Top Right of Map Area, not HUD?)
    # User wanted HUD optimized. Let's place Restart inside HUD but at top right corner of the HUD area
    # Or keep it where it was but adjust z-order/position to not overlap Constellation
    # Original: btn_restart_level = Button(WINDOW_WIDTH - 120, 70, 100, 30, ...)
    # This overlaps with the HUD header area (0-80). 
    # Let's move it to top-right of HUD (below header) or inside header.
    # Header is 0-80. 
    # HUD starts at MAP_WIDTH.
    btn_restart_level = Button(WINDOW_WIDTH - 110, 20, 90, 40, "回滚时间", cb_restart_level, (100, 100, 120))
    
    btn_close_report = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 300, 200, 50, "关闭显示", cb_close_analysis, (150, 50, 50))
    btn_exit_hidden = Button(20, 90, 100, 40, "退出", cb_exit_hidden, (150, 50, 50)) # Moved down to avoid overlap
    btn_sat_basic = Button(MAP_WIDTH + 20, 110, HUD_WIDTH - 40, 44, "基础卫星", cb_sat_pick_basic, (45, 65, 80))
    btn_sat_advanced = Button(MAP_WIDTH + 20, 162, HUD_WIDTH - 40, 44, "高级卫星", cb_sat_pick_advanced, (45, 65, 80))
    btn_sat_laser = Button(MAP_WIDTH + 20, 214, HUD_WIDTH - 40, 44, "激光卫星", cb_sat_pick_laser, (45, 65, 80))
    btn_sat_confirm = Button(MAP_WIDTH + 20, WINDOW_HEIGHT - 170, HUD_WIDTH - 40, 46, "确认发射", cb_sat_confirm, (40, 120, 80))
    btn_sat_skip = Button(MAP_WIDTH + 20, WINDOW_HEIGHT - 116, (HUD_WIDTH - 50) // 2, 44, "跳过部署", cb_sat_skip, (70, 70, 90))
    btn_sat_done = Button(MAP_WIDTH + 30 + (HUD_WIDTH - 50) // 2, WINDOW_HEIGHT - 116, (HUD_WIDTH - 50) // 2, 44, "完成部署", cb_sat_done, (70, 100, 140))

    while True:
        frame_counter += 1
        level = level_mgr.get_current_level()
        # Music Controller logic based on current state and level
        if current_state == STATE_START_SCREEN:
            play_bgm("ofeliasdream.mp3")
        elif current_state in [STATE_BRIEFING, STATE_TECH_UNLOCK, STATE_PLAYING] and level:
            play_bgm(get_level_music(level.get('id', 0)))
        elif current_state == STATE_CREDITS:
            play_bgm("ofeliasdream.mp3")
        elif current_state in [STATE_INTRO_1, STATE_INTRO_2]:
            play_bgm(None) # 静音
        elif current_state == STATE_LEVEL_CATALOG:
            play_bgm("ofeliasdream.mp3")

        if not level and current_state not in [STATE_CREDITS, STATE_INTRO_1, STATE_INTRO_2, STATE_LEVEL_CATALOG]: break
        
        if level:
            # First frame of Level 1 might require None for tutorial reset
            is_tutorial_level = (level.get('id') == 1)
            
            # Mod Enforcement
            if is_tutorial_level and current_mod is None:
                pass
            elif current_mod not in level['available_mods']: 
                current_mod = level['available_mods'][0]

            # Code Enforcement
            if is_tutorial_level and current_code is None:
                pass
            elif current_code not in level.get('available_codes', ["None"]): 
                current_code = "None"

        if current_state == STATE_PLAYING and is_animating:
            anim_progress += 0.02
            if anim_progress >= 1.0:
                anim_progress = 1.0
                is_animating = False
                finish_sim()
        if current_state == STATE_PLAYING and causal_animation and causal_animation.is_playing():
            causal_animation.update()

        # Events
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            # 成就小型通知：点击可提前关闭当前条（可选，不阻塞故一般不处理）
            if e.type == pygame.MOUSEWHEEL and current_state == STATE_ACHIEVEMENTS:
                global g_achievement_scroll_y
                g_achievement_scroll_y = max(0, g_achievement_scroll_y - e.y * 48)
            if e.type == pygame.MOUSEWHEEL and current_state == STATE_PLAYING:
                mx, _ = pygame.mouse.get_pos()
                if mx >= MAP_WIDTH:
                    hud_scroll_y = max(0, min(hud_scroll_max, hud_scroll_y - e.y * 36))
            
            # --- Intro States Logic ---
            if current_state in [STATE_INTRO_1, STATE_INTRO_2]:
                if e.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    # 任意键跳过当前 Intro 阶段
                    if current_state == STATE_INTRO_1:
                        current_state = STATE_INTRO_2
                        g_intro_alpha = 0
                        g_intro_timer = 0
                    else:
                        cb_skip_intro()
            
            if current_state == STATE_START_SCREEN:
                btn_new_game.handle_event(e)
                btn_continue.handle_event(e)
                btn_level_catalog.handle_event(e)
                btn_kv.handle_event(e)
                btn_settings.handle_event(e)
                btn_achievements.handle_event(e)
            elif current_state == STATE_LEVEL_CATALOG:
                btn_catalog_back.handle_event(e)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for rect, idx in g_level_catalog_rects:
                        if rect.collidepoint(e.pos):
                            level_mgr.current_level_idx = idx
                            current_state = STATE_BRIEFING
                            current_level = level_mgr.get_current_level()
                            if current_level:
                                assign_pending_weather(current_level)
                                play_bgm(get_level_music(current_level.get('id', 0)))
                            break
            elif current_state == STATE_SETTINGS:
                if slider_vol.handle_event(e):
                    # Volume changed
                    pygame.mixer.music.set_volume(slider_vol.val)
                btn_settings_back.handle_event(e)
            elif current_state == STATE_ACHIEVEMENTS:
                btn_achievements_back.handle_event(e)
            
            elif current_state == STATE_KNOWLEDGE_MENU:
                btn_kv_back.handle_event(e)
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = e.pos
                    for rect, node_data in g_tech_tree_rects:
                        if rect.collidepoint((mx, my)) and node_data.get("unlocked") and node_data.get("detail_item"):
                            global g_current_knowledge_item
                            g_current_knowledge_item = node_data["detail_item"]
                            current_state = STATE_KNOWLEDGE_DETAIL
                            break
            
            elif current_state == STATE_KNOWLEDGE_DETAIL:
                btn_detail_back.handle_event(e)

            elif current_state == STATE_EDU_SHOWCASE:
                btn_next_edu.handle_event(e)

            elif current_state == STATE_BRIEFING:
                btn_mission.handle_event(e)
                btn_briefing_kv.handle_event(e)
                if level.get('id') == 'HIDDEN_SAT_ARRAY':
                    btn_exit_hidden.handle_event(e)
            elif current_state == STATE_SATELLITE_DEPLOYMENT:
                btn_sat_basic.handle_event(e)
                btn_sat_advanced.handle_event(e)
                btn_sat_laser.handle_event(e)
                btn_sat_confirm.handle_event(e)
                btn_sat_skip.handle_event(e)
                btn_sat_done.handle_event(e)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and sat_deployment is not None:
                    px1, px2 = sat_deployment.position_range["x"]
                    py1, py2 = sat_deployment.position_range["y"]
                    mx, my = e.pos
                    if px1 <= mx <= px2 and py1 <= my <= py2:
                        sat_selected_pos = (mx, my)
                        sat_message = f"已选位置: ({mx}, {my})"
            
            elif current_state == STATE_TECH_UNLOCK:
                btn_tech_ok.handle_event(e)
            
            elif current_state == STATE_LETTER_VIEW:
                msg_len = len(level.get('message', ""))
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if g_letter_scroll_idx < msg_len:
                        g_letter_scroll_idx = msg_len + 1 # Instant finish
                    else:
                        btn_letter_confirm.handle_event(e)
                else:
                    if g_letter_scroll_idx >= msg_len:
                         btn_letter_confirm.handle_event(e)

            elif current_state == STATE_CONCLUSION:
                btn_conclusion_ok.handle_event(e)
            
            elif current_state == STATE_CREDITS:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    current_state = STATE_START_SCREEN

            elif current_state == STATE_PLAYING:
                if e.type == pygame.TEXTINPUT and command_mode:
                    text = getattr(e, "text", "")
                    if text:
                        command_buffer = (command_buffer + text)[-24:]
                    continue
                if e.type == pygame.KEYDOWN:
                    if command_mode:
                        if e.key == pygame.K_ESCAPE:
                            command_mode = False
                            command_buffer = ""
                        elif e.key == pygame.K_BACKSPACE:
                            command_buffer = command_buffer[:-1]
                        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            if command_buffer.lower() == "pass":
                                command_mode = False
                                command_buffer = ""
                                command_feedback = "命令执行: pass"
                                command_feedback_until = pygame.time.get_ticks() + 1200
                                cheat_pass_current_level()
                                continue
                            command_feedback = f"未知命令: {command_buffer or '(空)'}"
                            command_feedback_until = pygame.time.get_ticks() + 1500
                            command_buffer = ""
                            command_mode = False
                        # In command mode, consume key events before gameplay logic.
                        continue
                    else:
                        ch = getattr(e, "unicode", "")
                        if e.key in (pygame.K_SLASH, pygame.K_KP_DIVIDE) or ch in ("/", "／"):
                            command_mode = True
                            command_buffer = ""
                            continue
                if causal_animation and causal_pending_send:
                    if causal_animation.is_playing():
                        continue
                    if causal_animation.is_finished():
                        if e.type == pygame.MOUSEBUTTONDOWN:
                            causal_pending_send = False
                            causal_animation = None
                            cb_run_sim(force_send=True)
                        continue
                # DEBUG CHEAT: F6 跳关
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F6 and not command_mode:
                    for idx, lvl in enumerate(level_mgr.levels):
                        if lvl.get('id') == 10:
                            level_mgr.current_level_idx = idx
                            path_indices = []
                            sim_result = None
                            level_complete = False
                            is_animating = False
                            has_laser_tech = True
                            level = level_mgr.get_current_level()
                            if level:
                                current_mod = level['available_mods'][0]
                                current_code = level.get('available_codes', ["None"])[0]
                                assign_pending_weather(level)
                            current_state = STATE_BRIEFING
                            break
                # 第一关教学：误码率步骤中”点击任意处以继续”（点击到”回滚时间”按钮时交给按钮处理，不视为继续）
                if e.type == pygame.MOUSEBUTTONDOWN and g_tutorial.active and not is_animating and level and not level_complete:
                    tsteps = level.get('tutorial_steps') or []
                    if tsteps and g_tutorial.step < len(tsteps) and tsteps[g_tutorial.step].get('highlight') == 'ber_display' and sim_result is not None:
                        if not btn_restart_level.rect.collidepoint(e.pos):
                            g_tutorial.completed = True
                            continue
                # 优先处理地图区域内的节点点击（建立链路），避免被按钮逻辑覆盖
                map_click_consumed = False
                if e.type == pygame.MOUSEBUTTONDOWN and not is_animating and level:
                    mx, my = e.pos
                    if mx < MAP_WIDTH and 'nodes' in level:
                        if e.button == 3:
                            path_indices = []
                            map_click_consumed = True
                        elif e.button == 1:
                            if ghost_cube_visible and ghost_cube_rect.collidepoint((mx, my)):
                                global g_was_level_complete
                                g_was_level_complete = level_complete
                                hidden_lvl = generate_hidden_satellite_level()
                                global g_original_level
                                g_original_level = level_mgr.levels[level_mgr.current_level_idx]
                                level_mgr.levels[level_mgr.current_level_idx] = hidden_lvl
                                assign_pending_weather(hidden_lvl)
                                current_state = STATE_BRIEFING
                                path_indices = []
                                is_animating = False
                                level_complete = False
                                sim_result = None
                                map_click_consumed = True
                            else:
                                NODE_HIT_RADIUS = 28  # 节点可点击半径，略大于绘制半径便于操作
                                hit_radius_sq = NODE_HIT_RADIUS * NODE_HIT_RADIUS
                                for idx, node in enumerate(level['nodes']):
                                    dx = mx - node['pos'][0]
                                    dy = my - node['pos'][1]
                                    if dx * dx + dy * dy < hit_radius_sq:
                                        if not path_indices:
                                            if node['type'] == 'src':
                                                path_indices.append(idx)
                                                map_click_consumed = True
                                        else:
                                            if idx != path_indices[-1]:
                                                path_indices.append(idx)
                                                map_click_consumed = True
                                        break

                if not map_click_consumed:
                    power_slider.handle_event(e)
                    btn_restart_level.handle_event(e)
                    if level and level.get('id') == 'HIDDEN_SAT_ARRAY':
                        btn_exit_hidden.handle_event(e)
                    if show_analysis:
                        btn_close_report.handle_event(e)
                    elif not is_animating:
                        if not level_complete or (level and level.get('id') == 'HIDDEN_SAT_ARRAY'):
                            btn_tx.handle_event(e)
                        btn_knowledge.handle_event(e)
                        if sim_result:
                            btn_analysis.handle_event(e)
                        if e.type == pygame.MOUSEBUTTONDOWN:
                            mx, my = e.pos
                            for rect, m in ui_mod_rects:
                                if rect.collidepoint((mx, my)): set_mod(m)
                            for rect, c in ui_code_rects:
                                if rect.collidepoint((mx, my)): set_code(c)
                            for rect, proto in ui_protocol_rects:
                                if rect.collidepoint((mx, my)):
                                    set_protocol(proto)
                            for rect, d_method in ui_decoder_rects:
                                if rect.collidepoint((mx, my)): set_polar_method(d_method)
                            for rect, tech in ui_tech_rects:
                                if rect.collidepoint((mx, my)) and tech == "Laser":
                                    toggle_laser()

                if level_complete and level and level.get('id') != 'HIDDEN_SAT_ARRAY':
                    btn_next.handle_event(e)

        # Draw
        if current_state == STATE_START_SCREEN:
            draw_start_screen(screen, btn_new_game, btn_continue, btn_level_catalog, btn_kv, btn_settings, btn_achievements)
        elif current_state == STATE_LEVEL_CATALOG:
            draw_level_catalog(screen, level_mgr, g_level_stars, btn_catalog_back)
        elif current_state in [STATE_INTRO_1, STATE_INTRO_2]:
            g_intro_timer += 1
            # 简单的生命周期：Fade In (60帧) -> Hold (120帧) -> Fade Out (60帧)
            if g_intro_timer < 60:
                g_intro_alpha = int((g_intro_timer / 60) * 255)
            elif g_intro_timer < 180:
                g_intro_alpha = 255
            elif g_intro_timer < 240:
                g_intro_alpha = int(255 - ((g_intro_timer - 180) / 60) * 255)
            else:
                # 自动进入下一阶段
                if current_state == STATE_INTRO_1:
                    current_state = STATE_INTRO_2
                    g_intro_alpha = 0
                    g_intro_timer = 0
                else:
                    cb_skip_intro()
            
            txt = "HOPE IS A WAVEFORM" if current_state == STATE_INTRO_1 else "IS ANYONE OUT THERE?"
            col = (100, 200, 255) if current_state == STATE_INTRO_1 else (255, 255, 255)
            draw_intro_screen(screen, txt, col, max(0, min(255, g_intro_alpha)))

        elif current_state == STATE_SETTINGS:
            draw_settings_screen(screen, btn_settings_back, slider_vol)
        
        elif current_state == STATE_KNOWLEDGE_MENU:
            draw_knowledge_menu(screen, btn_kv_back, level_mgr, level_mgr.current_level_idx)
        
        elif current_state == STATE_KNOWLEDGE_DETAIL:
            draw_knowledge_detail(screen, btn_detail_back)
        elif current_state == STATE_ACHIEVEMENTS:
            draw_achievements_screen(screen, btn_achievements_back)
        elif current_state == STATE_EDU_SHOWCASE:
            draw_edu_showcase_screen(screen, btn_next_edu)

        elif current_state == STATE_BRIEFING:
            draw_briefing_screen(screen, level, btn_mission)
            btn_briefing_kv.draw(screen)
            if level.get('id') == 'HIDDEN_SAT_ARRAY':
                btn_exit_hidden.draw(screen)
        elif current_state == STATE_SATELLITE_DEPLOYMENT:
            if sat_deployment is not None:
                draw_satellite_deployment_screen(
                    screen,
                    level,
                    sat_deployment,
                    sat_selected_type,
                    sat_selected_pos,
                    sat_message,
                    btn_sat_confirm,
                    btn_sat_skip,
                    btn_sat_done,
                )
                btn_sat_basic.draw(screen)
                btn_sat_advanced.draw(screen)
                btn_sat_laser.draw(screen)
            else:
                current_state = STATE_BRIEFING
        elif current_state == STATE_TECH_UNLOCK:
            draw_tech_unlock_screen(screen, g_tech_unlock_level, btn_tech_ok)
        elif current_state == STATE_LETTER_VIEW:
            g_letter_scroll_idx += 2 # Speed of typing
            # 只有当显示完所有字时，才显示按钮
            # 在 draw_letter_view 内部判断
            draw_letter_view(screen, level, btn_letter_confirm)
        elif current_state == STATE_CONCLUSION:
            draw_conclusion_screen(screen, g_conclusion_level.get('id', 0) if g_conclusion_level else 0, btn_conclusion_ok)
        elif current_state == STATE_CREDITS:
            draw_credits_screen(screen)
        elif current_state == STATE_PLAYING:
            # Update Node Dynamics (Planets Orbiting)
            # Only move if not currently animating signal to keep visual consistent with calculation snapshot
            if not is_animating and not level_complete:
                lvl_id = level.get("id", 0)
                # Phase II maps are heavy; update every other frame to reduce stutter.
                if isinstance(lvl_id, int) and lvl_id >= 7:
                    if frame_counter % 2 == 0:
                        update_planet_dynamics(level)
                else:
                    update_planet_dynamics(level)
            
            ui_mod_rects.clear(); ui_code_rects.clear(); ui_protocol_rects.clear(); ui_tech_rects.clear()
            screen.fill(BG_COLOR)
            
            # Map Background
            pygame.draw.rect(screen, MAP_BG_COLOR, (0, 80, MAP_WIDTH, 800))
            
            # --- VFX: Starfield & Grid ---
            vfx_stars.update()
            vfx_stars.draw(screen)
            
            # Earth Background (Behind grid, front of stars)
            vfx_earth.draw(screen)

            vfx_grid.update()
            vfx_grid.draw(screen)
            
            # Radar Pings (Behind nodes but on top of map)
            vfx_radar.update()
            vfx_radar.draw(screen)
            
            # --- Ghost Cube (Hidden Trigger) ---
            if not is_animating and not level_complete:
                 update_ghost_cube(clock.get_time(), level.get('id', 0))
                 draw_ghost_cube(screen)

            # --- Dynamic Node Drawing ---
            if 'nodes' in level:
                 # Draw Connections (Pulsing Effect)
                if len(path_indices) > 0:
                    points = [level['nodes'][i]['pos'] for i in path_indices]
                    if len(points) > 1:
                        # 1. Base Line (Dimmer)
                        pygame.draw.lines(screen, (0, 80, 150), False, points, 3) # Darker base
                        
                        # 2. Moving Pulses
                        t = pygame.time.get_ticks() / 1000.0
                        pulse_speed = 200 # px per second
                        
                        for k in range(len(points) - 1):
                            p1 = points[k]
                            p2 = points[k+1]
                            dx = p2[0] - p1[0]
                            dy = p2[1] - p1[1]
                            dist = math.hypot(dx, dy)
                            
                            if dist < 1: continue
                            
                            dir_x = dx / dist
                            dir_y = dy / dist
                            
                            # Number of pulses on this segment based on distance
                            num_pulses = min(3, max(1, int(dist / 140)))
                            
                            for i in range(num_pulses):
                                # Calculate progress (0.0 to 1.0) based on time and index
                                progress = ((t * pulse_speed + i * (dist/num_pulses)) % dist) / dist
                                cur_x = p1[0] + dx * progress
                                cur_y = p1[1] + dy * progress
                                
                                # Draw Pulse (Head is bright, tail is transparent-ish)
                                # Simple: Bright circle
                                pygame.draw.circle(screen, (100, 200, 255), (int(cur_x), int(cur_y)), 3)
                                # Trail
                                trail_len = 15
                                trail_end_x = cur_x - dir_x * trail_len
                                trail_end_y = cur_y - dir_y * trail_len
                                pygame.draw.line(screen, (0, 150, 255), (int(cur_x), int(cur_y)), (int(trail_end_x), int(trail_end_y)), 2)

                    # Draw rubber band line if not finished
                    last_node_idx = path_indices[-1]
                    last_node = level['nodes'][last_node_idx]
                    
                    if last_node['type'] != 'dest' and not is_animating:
                        mx, my = pygame.mouse.get_pos()
                        pygame.draw.line(screen, (100, 100, 100), last_node['pos'], (mx, my), 1)
                        
                        # Determine hovered node for Matrix SNR preview
                        hover_idx = None
                        hover_r2 = 20 * 20
                        for idx, node in enumerate(level['nodes']):
                            ddx = mx - node['pos'][0]
                            ddy = my - node['pos'][1]
                            if ddx * ddx + ddy * ddy < hover_r2:
                                hover_idx = idx
                                break
                        
                        # 开启调试模式：显示实时预览 SNR
                        # 注意：隐藏关不显示 SNR，由玩家盲测
                        if level.get('id') != 'HIDDEN_SAT_ARRAY':
                            snr_temp = calculate_path_snr(
                                last_node['pos'],
                                (mx, my),
                                power_slider.current_power,
                                level=level,
                                idx1=last_node_idx,
                                idx2=hover_idx,
                            )
                            
                            color_snr = (255, 200, 50) if hover_idx is not None else (150, 150, 150)
                            snr_surf = font.render(f"Link SNR: {snr_temp:.1f}dB", True, color_snr)
                            
                            screen.blit(snr_surf, (mx+10, my+10))

            # Draw Obstacles (Level 8, 9, 10)
            if 'obstacles' in level:
                for obs in level['obstacles']:
                    pos = obs['pos']
                    size = obs.get('size', 10)
                    
                    # Generate polygon vertices if not present
                    if 'poly_points' not in obs:
                         obs['poly_points'] = generate_asteroid_polygon(size)
                         obs['rotation'] = np.random.rand() * 2 * np.pi
                         obs['rot_speed'] = np.random.uniform(-0.02, 0.02)
                    
                    # Update rotation
                    obs['rotation'] += obs['rot_speed']
                    
                    if level['id'] == 9: # Asteroids (碎石带)
                        color = (80, 70, 60)
                        outline = (100, 90, 80)
                    elif level['id'] == 10: # Ice chunks (深渊凝视)
                        color = (130, 180, 220, 200) # Light Blue
                        outline = (180, 220, 255)
                    elif level['id'] == 11: # Solar/Tech (昆仑)
                        if obs.get('type') == 'solar':
                            color = (255, 100, 50) # Orange
                            outline = (255, 200, 50)
                            # Pulse effect
                            size = size + np.sin(pygame.time.get_ticks()*0.01)*2
                            # Solar storms might just be circles still, or spiky polygons
                        else: # Swarm
                            color = (220, 40, 40) # Red
                            outline = (255, 100, 100)
                    else:
                        color = (100, 100, 100)
                        outline = (150, 150, 150)
                    
                    # Draw Poly
                    # Level 9 uses circles for better frame-time stability in chapter II.
                    if level['id'] in [10] or (level['id'] == 11 and obs.get('type') != 'solar'):
                        # Transform points
                        rot_points = []
                        cx, cy = pos
                        cos_a = np.cos(obs['rotation'])
                        sin_a = np.sin(obs['rotation'])
                        
                        for px, py in obs['poly_points']:
                            # Rotate then translate
                            rx = px * cos_a - py * sin_a
                            ry = px * sin_a + py * cos_a
                            rot_points.append((cx + rx, cy + ry))
                        
                        if len(rot_points) > 2:
                            pygame.draw.polygon(screen, color, rot_points)
                            pygame.draw.polygon(screen, outline, rot_points, 1)
                    else:
                         # Fallback for Solar Storms (Soft Circles)
                         pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), int(size))
                         # Glow
                         pygame.draw.circle(screen, (color[0], color[1], color[2], 50), (int(pos[0]), int(pos[1])), int(size+4), 1)

            # Draw Nodes
            if 'nodes' in level:
                for i, node in enumerate(level['nodes']):
                    # Add random radar ping to nodes
                    vfx_radar.add(node['pos'][0], node['pos'][1])

                    color = (100, 255, 100) # Default
                    if node['type'] == 'src': color = (100, 255, 255)
                    elif node['type'] == 'dest': color = (255, 100, 100)
                    elif node['type'] == 'relay': color = (200, 200, 100)
                    
                    if i in path_indices:
                        pygame.draw.circle(screen, (255, 255, 255), node['pos'], 8) # Selected highlight
                        # Add constant ping for selected nodes
                        if np.random.random() < 0.1: vfx_radar.add(node['pos'][0], node['pos'][1])
                    
                    pygame.draw.circle(screen, color, node['pos'], 6)
                    
                    # Label
                    text = font.render(node['name'], True, (200, 200, 200))
                    rect = text.get_rect(center=(node['pos'][0], node['pos'][1] + 20))
                    pygame.draw.rect(screen, (0,0,0,150), rect.inflate(10,4), border_radius=3)
                    screen.blit(text, rect)
            else:
                # Legacy Drawing
                p0, p1, p2 = level['source_pos'], level['curve_control'], level['dest_pos']
                
                # Add Radar Pings for legacy nodes
                vfx_radar.add(p0[0], p0[1])
                vfx_radar.add(p2[0], p2[1])

                draw_map_connection(screen, p0, p1, p2, anim_progress, active=is_animating)
                draw_node(screen, p0, level['source_name'], False)
                draw_node(screen, p2, level['dest_name'], True)
            
            # 背景噪声视觉效果：除第一关外全部开启，或根据是否有节点判定
            if level.get('id') != 1:
                for _ in range(50):
                     pygame.draw.circle(screen, (40,50,60), (np.random.randint(0,MAP_WIDTH), np.random.randint(105,800)), 1)

            # Header：横线下移，关卡内容整体下移，顶栏加高留白
            header_h = 100
            left_x = 20
            line1_y, line2_y = 18, 48
            pygame.draw.rect(screen, PANEL_COLOR, (0, 0, WINDOW_WIDTH, header_h))
            # 左：阶段+标题（第一行），目标 BER | SNR（第二行）
            phase_title = f"{level['phase']} : {level['title']}"
            max_title_w = MAP_WIDTH - 320
            title_surf = header_font.render(phase_title, True, ACCENT_COLOR)
            if title_surf.get_width() > max_title_w:
                phase_title = phase_title[:20] + "…" if len(phase_title) > 20 else phase_title
                title_surf = header_font.render(phase_title, True, ACCENT_COLOR)
            screen.blit(title_surf, (left_x, line1_y))
            if 'nodes' in level:
                snr_display = "Varies (Dist)"
                if sim_result and 'final_snr' in sim_result:
                    snr_display = f"Last Hop {sim_result['final_snr']:.1f}dB"
            else:
                snr_display = "No noise" if level.get('id') == 1 else f"{level['snr_db']}dB"
            screen.blit(font.render(f"目标 BER < {level['target_ber']}  |  SNR: {snr_display}", True, (150,150,150)), (left_x, line2_y))
            # 横线再下移，与文字、关卡内容留足间距
            sep_y = 82
            pygame.draw.line(screen, (50, 55, 65), (0, sep_y), (MAP_WIDTH, sep_y), 1)
            # 右：预算 + 天气 + 回滚按钮
            pwr_x = MAP_WIDTH - 220
            budget_surf = label_font.render(
                f"预算: {fmt_num(budget_manager.current_budget)}  已消耗: {fmt_num(budget_manager.spent_this_level)}",
                True,
                (255, 215, 120),
            )
            screen.blit(budget_surf, (pwr_x - 120, line1_y + 8))
            weather_name = weather_system.get_weather_info().name
            weather_surf = label_font.render(f"天气: {weather_name}", True, (170, 210, 255))
            screen.blit(weather_surf, (pwr_x - 120, line2_y + 12))
            if level.get('id') != 'HIDDEN_SAT_ARRAY':
                btn_restart_level.draw(screen)

            # Weather panel (from implementation checklist): visible summary on map side.
            weather_info = weather_system.get_weather_info()
            panel_rect = pygame.Rect(20, 92, 320, 84)
            pygame.draw.rect(screen, (22, 28, 36), panel_rect, border_radius=8)
            pygame.draw.rect(screen, (70, 100, 130), panel_rect, 1, border_radius=8)
            screen.blit(label_font.render(f"天气: {weather_info.name}", True, (180, 220, 255)), (panel_rect.x + 12, panel_rect.y + 8))
            screen.blit(label_font.render(weather_info.description, True, (195, 205, 215)), (panel_rect.x + 12, panel_rect.y + 30))
            screen.blit(
                label_font.render(f"SNR {weather_info.snr_penalty:+.1f} dB | BER x{weather_info.ber_multiplier:.2f}", True, (150, 180, 210)),
                (panel_rect.x + 12, panel_rect.y + 52),
            )

            # Hidden Level Special UI: Attempts
            if level.get('id') == 'HIDDEN_SAT_ARRAY':
                attempts_left = MAX_HIDDEN_ATTEMPTS - hidden_attempts
                att_color = (255, 200, 50) if attempts_left > 0 else (255, 50, 50)
                screen.blit(font.render(f"Remaining Pings: {attempts_left}", True, att_color), (WINDOW_WIDTH - 220, 60))
            
            # HUD Background (Fills the right side)
            bx = MAP_WIDTH
            pygame.draw.rect(screen, (25, 25, 30), (bx, 0, HUD_WIDTH, WINDOW_HEIGHT))
            pygame.draw.line(screen, ACCENT_COLOR, (bx, 0), (bx, WINDOW_HEIGHT), 2)
            hud_content_clip = pygame.Rect(bx, 92, HUD_WIDTH, WINDOW_HEIGHT - 92)
            screen.set_clip(hud_content_clip)
            
            # --- 1. Constellation Monitor (Moved UP) ---
            cy_base = 40 - hud_scroll_y
            screen.blit(label_font.render("星图投影 (Star Chart)", True, ACCENT_COLOR), (bx + 15, cy_base))
            
            cy_box = cy_base + 20 # 105
            c_box_h = 160 # Reduced slightly
            pygame.draw.rect(screen, (0, 0, 0), (bx + 10, cy_box, HUD_WIDTH - 20, c_box_h), border_radius=5)
            pygame.draw.rect(screen, (60, 60, 70), (bx + 10, cy_box, HUD_WIDTH - 20, c_box_h), 1, border_radius=5)
            
            if sim_result:
                draw_constellation(screen, sim_result['rx_syms'], bx + HUD_WIDTH//2, cy_box + c_box_h//2, 60)
            else:
                cx_c, cy_c = bx + HUD_WIDTH//2, cy_box + c_box_h//2
                pygame.draw.line(screen,(40,40,40),(cx_c - 100, cy_c),(cx_c + 100, cy_c))
                pygame.draw.line(screen,(40,40,40),(cx_c, cy_c - 60),(cx_c, cy_c + 60))
                
            # --- 2. System Configuration ---
            y = cy_box + c_box_h + 20 # ~ 285
            screen.blit(label_font.render("阵列配置 (Array Config)", True, ACCENT_COLOR), (bx+10, y))
            y += 25
            
            # Mod Selection
            screen.blit(label_font.render("MODULATION", True, (150,150,150)), (bx+10, y+8))
            mods = level.get('available_mods', ["BPSK"])
            btn_w = (HUD_WIDTH - 80) // len(mods) if mods else HUD_WIDTH - 40
            for i,mod in enumerate(mods):
                r = pygame.Rect(bx+60+i*(btn_w+5), y, btn_w, 30)
                ui_mod_rects.append((r,mod))
                
                # --- TUTORIAL CAPTURE: BPSK Button ---
                if mod == "BPSK": rect_mod_bpsk = r
                
                col = (0, 120, 200) if mod == current_mod else (50,50,60)
                pygame.draw.rect(screen, col, r, border_radius=4)
                if mod == current_mod: pygame.draw.rect(screen, (255,255,255), r, 1, border_radius=4)
                
                txt = label_font.render(mod, True, (255,255,255))
                screen.blit(txt, (r.centerx-txt.get_width()//2, r.centery-txt.get_height()//2))
            
            # Coding Selection
            y += 35
            screen.blit(label_font.render("CODE", True, (150,150,150)), (bx+10, y+8))
            codes = level.get('available_codes', ["None"])
            for i,code in enumerate(codes):
                # Spread out in grid if many
                cols = 2 if len(codes) > 2 else len(codes)
                row = i // cols
                col_idx = i % cols
                btn_w = (HUD_WIDTH - 80) // cols
                
                # If we have multiple lines, increment y for each new row
                current_y = y + row * 35
                
                r = pygame.Rect(bx+60+col_idx*(btn_w+5), current_y, btn_w, 30)

                # --- TUTORIAL CAPTURE: Code Button ---
                if code == "Repetition(3,1)": rect_code_rep = r

                ui_code_rects.append((r,code))
                col = (180,80,30) if code == current_code else (50,50,60)
                pygame.draw.rect(screen, col, r, border_radius=4)
                if code == current_code: pygame.draw.rect(screen, (255,255,255), r, 1, border_radius=4)
                
                txt = label_font.render(code, True, (255,255,255))
                screen.blit(txt, (r.centerx-txt.get_width()//2, r.centery-txt.get_height()//2))

            # Adjust y based on how many rows code buttons took
            num_rows_code = (len(codes) + 1) // 2 if len(codes) > 0 else 1
            y += num_rows_code * 35 + 10

            # Protocol Selection (Phase 2.1)
            screen.blit(label_font.render("PROTOCOL", True, (150,150,150)), (bx+10, y+8))
            level_id = level.get("id")
            safe_level_id = level_id if isinstance(level_id, int) else 1
            available_protocols = protocol_system.get_available_protocols(safe_level_id)
            proto_items = list(available_protocols.items())
            proto_cols = min(2, max(1, len(proto_items)))
            proto_w = (HUD_WIDTH - 80) // proto_cols
            for i, (proto_id, proto_info) in enumerate(proto_items):
                row = i // proto_cols
                col_idx = i % proto_cols
                py = y + row * 35
                r = pygame.Rect(bx + 60 + col_idx * (proto_w + 5), py, proto_w, 30)
                ui_protocol_rects.append((r, proto_id))
                selected = proto_id == selected_protocol
                col = (20, 110, 120) if selected else (50, 50, 60)
                pygame.draw.rect(screen, col, r, border_radius=4)
                if selected:
                    pygame.draw.rect(screen, (255, 255, 255), r, 1, border_radius=4)
                ptxt = label_font.render(f"{proto_info.name} ({fmt_num(proto_info.cost)})", True, (235, 235, 235))
                screen.blit(ptxt, (r.centerx - ptxt.get_width() // 2, r.centery - ptxt.get_height() // 2))
            proto_rows = (len(proto_items) + proto_cols - 1) // proto_cols
            y += proto_rows * 35 + 8

            # Weather / Power controls (Phase 1.2 + 2.3.1)
            w_info = weather_system.get_weather_info()
            weather_cycle_rect = pygame.Rect(bx + 10, y, HUD_WIDTH - 20, 28)
            pygame.draw.rect(screen, (55, 65, 80), weather_cycle_rect, border_radius=4)
            pygame.draw.rect(screen, (110, 130, 160), weather_cycle_rect, 1, border_radius=4)
            wtxt = label_font.render(f"天气: {w_info.name}  (本关随机固定)", True, (215, 230, 255))
            screen.blit(wtxt, (weather_cycle_rect.x + 10, weather_cycle_rect.centery - wtxt.get_height() // 2))
            y += 34

            power_slider.y = y
            slider_rect = power_slider.rect
            pygame.draw.rect(screen, (55, 55, 60), slider_rect, border_radius=4)
            ratio = power_slider.get_ratio()
            handle_x = slider_rect.x + int(ratio * slider_rect.width)
            pygame.draw.circle(screen, (0, 180, 255), (handle_x, slider_rect.centery), 10)
            ptxt = label_font.render(
                f"发射功率: {power_slider.current_power:.1f} dBm  成本: {fmt_num(calculate_transmission_cost(power_slider.current_power, selected_protocol))}",
                True,
                (190, 220, 250),
            )
            screen.blit(ptxt, (bx + 10, y + 30))
            y += 56

            # System Status
            screen.blit(label_font.render("系统状态 (System Status)", True, ACCENT_COLOR), (bx+10, y))
            y += 25
            screen.blit(font.render(f"可用预算: {fmt_num(budget_manager.current_budget)}", True, (255, 200, 50)), (bx+20, y))
            y += 30

            # Decoder / Tech Row
            if current_code and current_code.startswith("Polar"):
                screen.blit(label_font.render("DEC:", True, (150,150,150)), (bx+10, y+5))
                methods = ["SC"]
                lvl_id = level.get('id', 1)
                if (isinstance(lvl_id, int) and lvl_id >= 7) or isinstance(lvl_id, str): methods.append("BP")
                if (isinstance(lvl_id, int) and lvl_id >= 7) or isinstance(lvl_id, str): methods.append("SCL")
                
                for j, method in enumerate(methods):
                    rect_d = pygame.Rect(bx + 60 + j*75, y, 70, 25)
                    ui_decoder_rects.append((rect_d, method))
                    col_d = (40, 120, 80) if current_polar_method == method else (40, 40, 50)
                    pygame.draw.rect(screen, col_d, rect_d, border_radius=4)
                    if current_polar_method == method: pygame.draw.rect(screen, (255, 255, 255), rect_d, 1, border_radius=4)
                    txt_d = label_font.render(method, True, (255,255,255))
                    screen.blit(txt_d, (rect_d.centerx - txt_d.get_width()//2, rect_d.centery - txt_d.get_height()//2))
                y += 40
            
            # Laser Tech (Unlock Check: Level >= 6)
            if isinstance(level.get('id', 0), int) and level.get('id', 0) >= 7:
                has_laser_tech = True
            
            if has_laser_tech:
                r_tech = pygame.Rect(bx+10, y, HUD_WIDTH-20, 30)
                ui_tech_rects.append((r_tech, "Laser"))
                col_t = (180, 30, 30) if laser_module_active else (60, 60, 65)
                pygame.draw.rect(screen, col_t, r_tech, border_radius=4)
                if laser_module_active: pygame.draw.rect(screen, (255, 100, 100), r_tech, 1, border_radius=4)
                
                status_str = "LASER MODULE: ACTIVE (+120预算)" if laser_module_active else "LASER MODULE: STANDBY"
                t_surf = label_font.render(status_str, True, (255,255,255))
                screen.blit(t_surf, (r_tech.centerx - t_surf.get_width()//2, r_tech.centery - t_surf.get_height()//2))
                y += 40

            y += 10 # Spacer

            # --- 2.5 当前配置预览 (阶段 2.1) ---
            preview_h = 100
            pygame.draw.rect(screen, (18, 22, 28), (bx+10, y, HUD_WIDTH-20, preview_h), border_radius=6)
            pygame.draw.rect(screen, (50, 60, 75), (bx+10, y, HUD_WIDTH-20, preview_h), 1, border_radius=6)
            screen.blit(label_font.render("当前配置预览", True, ACCENT_COLOR), (bx+18, y+6))
            snr_preview = level.get('snr_db', 5) + compute_power_snr_boost(power_slider.current_power)
            est_ber = estimate_ber(snr_preview, current_mod or "BPSK", current_code)
            target_ber = level['target_ber']
            star_num = estimate_stars(est_ber, target_ber)
            screen.blit(
                label_font.render(
                    f"调制: {current_mod or '—'}  编码: {current_code or '—'}  协议: {selected_protocol.upper()}",
                    True,
                    (200,200,200),
                ),
                (bx+18, y+26),
            )
            screen.blit(label_font.render(f"预计误码率: ~{est_ber:.4f}", True, (180,200,180)), (bx+18, y+46))
            star_str = "★" * star_num + "☆" * (5 - star_num)
            screen.blit(label_font.render(f"建议: {star_str}", True, (255, 200, 50)), (bx+18, y+66))
            y += preview_h + 8

            # --- 3. Link Quality Monitor (Gauge) ---
            y_gauge = y + 5
            
            # --- TUTORIAL CAPTURE: Gauge ---
            rect_gauge = pygame.Rect(bx+10, y_gauge, HUD_WIDTH-20, 110)
            pygame.draw.rect(screen, (20,20,25), (bx+10, y_gauge, HUD_WIDTH-20, 110), border_radius=6)
            pygame.draw.rect(screen, (60,60,70), (bx+10, y_gauge, HUD_WIDTH-20, 110), 1, border_radius=6)
            screen.blit(label_font.render("回声解析 (Echo Analysis)", True, ACCENT_COLOR), (bx+20, y_gauge+10))
            
            # Target BER Marker
            target_ber = level['target_ber']
            curr_ber = sim_result['ber'] if sim_result else 1.0
            
            # Progress Bar for BER (Logarithmic scale since BER varies from 0.5 to 1e-6)
            def ber_to_width(b):
                if b <= 0: return 1.0
                return max(0, min(1.0, (np.log10(0.5) - np.log10(b)) / 6.0)) # Maps 0.5->0 to 5e-7->1

            bar_w = HUD_WIDTH - 60
            bar_rect = pygame.Rect(bx+30, y_gauge+40, bar_w, 20)
            pygame.draw.rect(screen, (40,40,45), bar_rect, border_radius=4)
            
            if sim_result:
                w = int(bar_w * ber_to_width(curr_ber))
                bar_col = SUCCESS_COLOR if curr_ber <= target_ber else ERROR_COLOR
                pygame.draw.rect(screen, bar_col, (bx+30, y_gauge+40, w, 20), border_radius=4)
            
            # Target tick
            target_x = bx+30 + int(bar_w * ber_to_width(target_ber))
            pygame.draw.line(screen, (255, 255, 255), (target_x, y_gauge+35), (target_x, y_gauge+65), 2)
            screen.blit(label_font.render("阈值", True, (255,255,255)), (target_x-15, y_gauge+67))
            
            # Numbers
            ber_str = f"{curr_ber:.4f}" if sim_result else "----"
            screen.blit(font.render(f"当前: {ber_str}", True, (220,220,220)), (bx+30, y_gauge+85))
            screen.blit(label_font.render(f"目标: <{target_ber}", True, (150,150,150)), (bx+HUD_WIDTH-120, y_gauge+88))
            # 三星评价显示 (2.2)：过关时显示本次获得的星级
            if level_complete and sim_result and sim_result.get('success'):
                stars = sim_result.get('stars', 0)
                GOLD, GRAY = (255, 200, 50), (80, 80, 80)
                screen.blit(label_font.render("本次星级:", True, GOLD), (bx+20, y_gauge+108))
                for i in range(3):
                    sx = bx + 120 + i * 22
                    if i < stars:
                        screen.blit(label_font.render("★", True, GOLD), (sx, y_gauge+105))
                    else:
                        screen.blit(label_font.render("☆", True, GRAY), (sx, y_gauge+105))
                # 阶段三 3.2 关卡评分详情
                brk = sim_result.get("score_breakdown", [])
                total_score = sim_result.get("total_score", 0)
                grade = sim_result.get("grade", "C")
                y_sc = y_gauge + 132
                screen.blit(label_font.render("关卡评分", True, (200, 220, 255)), (bx+20, y_sc))
                y_sc += 22
                for name, pts in brk:
                    screen.blit(label_font.render(f"  {name} +{pts}", True, SUCCESS_COLOR), (bx+20, y_sc))
                    y_sc += 18
                screen.blit(label_font.render(f"总分: {fmt_num(total_score)} / 200  评级: {grade}", True, GOLD), (bx+20, y_sc))
                y_sc += 24
                y_diag = y_sc + 10
            else:
                y_diag = y_gauge + 120

            # --- 4. Diagnostic Log / Signal History ---
            # Start below Link Quality or below score detail when level complete
            
            # Initialize log_lines
            log_lines = []
            if sim_result:
                if sim_result['success']:
                    log_lines = ["信号完整性：良好", "握手成功。正在同步星图...", "建议：当前配置已优化。"]
                else:
                    reason = sim_result.get('failure_reason', "链路建立失败。")
                    log_lines = [reason]
                    if "噪声" in reason: log_lines.append("建议：尝试更强的 Polar 码或 QPSK。")
                    elif "视线" in reason: log_lines.append("注意：传输路径被阻挡，检查中继。")
                    elif "能量" in reason: log_lines.append("注意：中继节点能量耗尽。")
            
            # Calculate max available height (leave space for buttons)
            # Buttons start at y = WINDOW_HEIGHT - 200 (Topmost Analysis button)
            # Let's give it a 20px padding; if score detail was drawn, y_diag was advanced
            y_buttons_top = WINDOW_HEIGHT - 200
            max_log_h = y_buttons_top - y_diag - 20
            
            log_box_h = max(100, max_log_h) 
            
            pygame.draw.rect(screen, (15,15,20), (bx+10, y_diag, HUD_WIDTH-20, log_box_h), border_radius=6)
            pygame.draw.rect(screen, (50,55,60), (bx+10, y_diag, HUD_WIDTH-20, log_box_h), 1, border_radius=6)
            
            # Using new name for the log area
            screen.blit(label_font.render("幻影回声追踪 (Ghost Echo Trace)", True, (255,200,50)), (bx+20, y_diag+10))
            
            diag_y = y_diag + 35
            
            # Use clipping to prevent overflow
            log_clip_rect = pygame.Rect(bx+12, diag_y, HUD_WIDTH-24, log_box_h - 40)
            screen.set_clip(log_clip_rect)
            
            if log_lines:
                for line in log_lines:
                    diag_y = render_text_wrapped(screen, f"> {line}", (bx+25, diag_y), HUD_WIDTH-50, label_font, (200,200,200))
                    diag_y += 2
                
                if sim_result and len(sim_result.get('steps', [])) > 0:
                    diag_y += 5
                    pygame.draw.line(screen, (60,60,70), (bx+20, diag_y), (bx+HUD_WIDTH-20, diag_y))
                    diag_y += 8
                    for step in sim_result['steps']:
                        quality = "OK" if step['ber_hop'] < 0.05 else "BAD"
                        col = SUCCESS_COLOR if quality == "OK" else ERROR_COLOR
                        txt = label_font.render(f"{step['from']}->{step['to']}: {step['snr']:.1f}dB ({quality})", True, col)
                        screen.blit(txt, (bx+25, diag_y))
                        diag_y += 18
            else:
                screen.blit(label_font.render("> 准备发射信号...", True, (100,100,100)), (bx+25, diag_y))
                screen.blit(label_font.render("> 检查视线 (LOS)...", True, (100,100,100)), (bx+25, diag_y+22))
            
            screen.set_clip(None)

            # 术语悬停提示 (1.2)：在 HUD 区域检测调制/编码按钮悬停
            if not is_animating:
                mouse_pos = pygame.mouse.get_pos()
                hover_tooltip = None
                for r, name in ui_mod_rects:
                    if r.collidepoint(mouse_pos):
                        hover_tooltip = TOOLTIPS.get(name, None)
                        break
                if hover_tooltip is None:
                    for r, name in ui_code_rects:
                        if r.collidepoint(mouse_pos):
                            hover_tooltip = TOOLTIPS.get(name, None)
                            break
                if hover_tooltip is None:
                    for r, name in ui_protocol_rects:
                        if r.collidepoint(mouse_pos):
                            hover_tooltip = TOOLTIPS.get(name, None)
                            break
                if hover_tooltip:
                    draw_tooltip(screen, hover_tooltip, mouse_pos, label_font)

            # Task Card (Repositioned to the Map Area)
            # 1. Pre-calculate height
            temp_y = 125
            for line in level['mission_text'].split('\n'):
                temp_y = render_text_wrapped(screen, line, (30, temp_y), 300, label_font, draw=False)
                temp_y += 2
            
            box_height = max(110, (temp_y - 90) + 10)
            c_rect = pygame.Rect(20, 90, 360, box_height)
            
            # Draw Background
            s = pygame.Surface((c_rect.width, c_rect.height), pygame.SRCALPHA)
            # --- TUTORIAL CAPTURE: TX Button ---
            rect_tx_btn = btn_tx.rect

            if not is_animating: 
                # 如果关卡未完成，或者是隐藏关（隐藏关没有下一关按钮），显示发射按钮
                if not level_complete or level.get('id') == 'HIDDEN_SAT_ARRAY':
                    btn_tx.draw(screen)
                
            if not is_animating: btn_knowledge.draw(screen)
            
            # 如果关卡完成且不是隐藏关，显示下一关按钮（替代发射按钮）
            if level_complete and level.get('id') != 'HIDDEN_SAT_ARRAY': 
                btn_next.draw(screen)
            
            if sim_result and not is_animating: btn_analysis.draw(screen)
            
            # Restart Button (Always visible in Playing unless restricted)
            if level.get('id') != 'HIDDEN_SAT_ARRAY':
                btn_restart_level.draw(screen)
            
            if level.get('id') == 'HIDDEN_SAT_ARRAY':
                btn_exit_hidden.draw(screen)

            # Analysis Overlay
            if show_analysis:
                draw_analysis_report(screen, sim_result, btn_close_report)

            # -------------------------------------------------------------
            # TUTORIAL RENDER LOGIC (教程逻辑，由关卡 tutorial_steps 驱动)
            if g_tutorial.active and not level_complete and current_state == STATE_PLAYING:
                tutorial_steps = level.get('tutorial_steps') or []
                if tutorial_steps and g_tutorial.step < len(tutorial_steps):
                    step_info = tutorial_steps[g_tutorial.step]
                    highlight = step_info.get('highlight', '')
                    text = step_info.get('text', '')
                    target_rect = pygame.Rect(100, 100, MAP_WIDTH - 200, 600)
                    if highlight == 'modulation_panel' or highlight == 'modulation':
                        target_rect = rect_mod_bpsk
                    elif highlight == 'coding_panel' or highlight == 'coding':
                        target_rect = rect_code_rep if rect_code_rep.width > 0 else pygame.Rect(bx+60, 340, 200, 40)
                    elif highlight == 'send_button':
                        target_rect = rect_tx_btn
                    elif highlight == 'ber_display':
                        target_rect = rect_gauge
                    g_tutorial.draw(screen, target_rect, text)
                    # 误码率步骤且已有结果时，显示“点击任意处以继续”
                    if highlight == 'ber_display' and sim_result is not None and not is_animating:
                        hint_surf = label_font.render("点击任意处以继续", True, (180, 220, 255))
                        hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
                        pygame.draw.rect(screen, (30, 40, 55), hint_rect.inflate(24, 12), border_radius=6)
                        pygame.draw.rect(screen, (80, 100, 120), hint_rect.inflate(24, 12), 1, border_radius=6)
                        screen.blit(hint_surf, hint_rect)
                    # 根据当前步骤检查是否可进入下一步
                    if highlight == 'path' and len(path_indices) >= 2:
                        g_tutorial.next()
                    elif (highlight == 'modulation_panel' or highlight == 'modulation') and current_mod == "BPSK":
                        g_tutorial.next()
                    elif (highlight == 'coding_panel' or highlight == 'coding') and current_code == "Repetition(3,1)":
                        g_tutorial.next()
                    elif highlight == 'send_button' and is_animating:
                        g_tutorial.next()
                    # ber_display 不在此处自动推进，仅通过“点击任意处以继续”在事件中推进，避免显示过快
                elif tutorial_steps and g_tutorial.step >= len(tutorial_steps):
                    g_tutorial.completed = True
            # -------------------------------------------------------------
            
            # 传输过程可视化 (2.3)：传输完成后显示统计覆盖层
            if sim_result and not is_animating and transmission_stats_until > 0 and pygame.time.get_ticks() < transmission_stats_until:
                ber = sim_result.get('ber', 0)
                total = 50
                correct = int(total * (1 - ber))
                error = total - correct
                box_w, box_h = 320, 140
                cx = MAP_WIDTH // 2
                cy = WINDOW_HEIGHT // 2
                box_rect = pygame.Rect(cx - box_w//2, cy - box_h//2, box_w, box_h)
                s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                s.fill((15, 18, 22, 230))
                pygame.draw.rect(s, (60, 70, 90), (0, 0, box_w, box_h), 2, border_radius=8)
                screen.blit(s, box_rect)
                screen.blit(header_font.render("传输完成", True, ACCENT_COLOR), (box_rect.x + 20, box_rect.y + 12))
                pygame.draw.line(screen, (60, 70, 90), (box_rect.x + 15, box_rect.y + 48), (box_rect.right - 15, box_rect.y + 48), 1)
                screen.blit(font.render(f"✓ 正确: {correct} 个", True, SUCCESS_COLOR), (box_rect.x + 25, box_rect.y + 58))
                screen.blit(font.render(f"✗ 错误: {error} 个", True, ERROR_COLOR), (box_rect.x + 25, box_rect.y + 82))
                screen.blit(font.render(f"最终误码率: {ber:.4f}", True, (220, 220, 220)), (box_rect.x + 25, box_rect.y + 106))
                progress = sim_result.get("segment_progress", 0.0)
                screen.blit(label_font.render(f"分段进度: {int(progress * 100)}%", True, (180, 220, 255)), (box_rect.x + 190, box_rect.y + 106))

            # Command bar: press "/" to open, input `pass` then Enter.
            now_ticks = pygame.time.get_ticks()
            if command_mode:
                cmd_w, cmd_h = 420, 46
                cmd_rect = pygame.Rect(MAP_WIDTH // 2 - cmd_w // 2, WINDOW_HEIGHT - 64, cmd_w, cmd_h)
                pygame.draw.rect(screen, (16, 22, 30), cmd_rect, border_radius=8)
                pygame.draw.rect(screen, (80, 120, 180), cmd_rect, 2, border_radius=8)
                cmd_text = f"/{command_buffer}"
                screen.blit(font.render(cmd_text, True, (220, 235, 255)), (cmd_rect.x + 14, cmd_rect.y + 11))
                screen.blit(label_font.render("输入命令后回车（ESC取消）", True, (160, 180, 210)), (cmd_rect.x, cmd_rect.y - 20))
            elif command_feedback and now_ticks < command_feedback_until:
                tip = label_font.render(command_feedback, True, (255, 215, 120))
                tip_rect = tip.get_rect(center=(MAP_WIDTH // 2, WINDOW_HEIGHT - 40))
                pygame.draw.rect(screen, (24, 28, 34), tip_rect.inflate(24, 10), border_radius=6)
                pygame.draw.rect(screen, (100, 120, 150), tip_rect.inflate(24, 10), 1, border_radius=6)
                screen.blit(tip, tip_rect)
            if causal_animation and causal_pending_send:
                causal_animation.draw(screen, font, label_font, header_font)
            hud_content_bottom = y_diag + log_box_h + hud_scroll_y
            hud_scroll_max = max(0, int(hud_content_bottom - (WINDOW_HEIGHT - 120)))
            screen.set_clip(None)

        # 阶段三 3.1：成就小型通知（成就.md 4.3，右上角滑入/2s 停留/滑出，不阻塞）
        update_achievement_notification(pygame.time.get_ticks())
        if g_achievement_notif_state:
            draw_achievement_notification(screen, font, label_font)

        pygame.display.flip()
        # 累计游戏时长（成就统计）
        g_game_stats["total_playtime"] = g_game_stats.get("total_playtime", 0) + clock.get_time() / 1000.0
        clock.tick(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Game terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pygame.quit()
        if 'sys' in locals():
            sys.exit()
