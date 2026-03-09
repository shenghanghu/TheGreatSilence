import os

# --- DSP ENGINE ---
dsp_code = r'''import numpy as np

class DSPEngine:
    """
    通信核心引擎：处理真实的比特流、编码、调制和信道模拟
    """
    
    # --- 基础工具 ---
    @staticmethod
    def str_to_bits(message):
        """将字符串转换为比特流"""
        # 使用 utf-8 编码以支持更多字符，如果失败回退到 latin1
        try:
            byte_data = message.encode('utf-8')
        except:
            byte_data = message.encode('latin1', errors='ignore')
            
        byte_array = np.frombuffer(byte_data, dtype=np.uint8)
        # unpackbits 默认是 big-endian (对于 uint8 来说)
        bits = np.unpackbits(byte_array)
        return bits

    @staticmethod
    def bits_to_str(bits):
        """将比特流还原为字符串，并过滤乱码"""
        # 补齐 8 的倍数
        rem = len(bits) % 8
        if rem != 0:
            bits = np.concatenate([bits, np.zeros(8 - rem, dtype=int)])
            
        bytes_data = np.packbits(bits)
        try:
            # 尝试解码
            txt = bytes_data.tobytes().decode('utf-8')
            # 过滤不可见字符
            clean_txt = ""
            for c in txt:
                if c.isprintable():
                    clean_txt += c
                else:
                    clean_txt += "?"
            return clean_txt
        except:
            return "?" * (len(bits) // 8)

    @staticmethod
    def calculate_ber(tx_bits, rx_bits):
        """计算误码率 Bit Error Rate"""
        min_len = min(len(tx_bits), len(rx_bits))
        if min_len == 0: return 1.0
        errors = np.sum(tx_bits[:min_len] != rx_bits[:min_len])
        return errors / min_len

    # --- 信道编码模块 (Channel Coding) ---
    
    @staticmethod
    def encode_data(bits, code_type):
        """信道编码"""
        if code_type == "None" or code_type is None:
            return bits
            
        elif code_type == "Repetition(3,1)":
            # 重复码
            return np.repeat(bits, 3)
            
        elif code_type == "Hamming(7,4)":
            # 简化版填充
            rem = len(bits) % 4
            if rem != 0:
                pad = 4 - rem
                bits = np.concatenate([bits, np.zeros(pad, dtype=int)])
            
            # G Matrix (7,4)
            G = np.array([
                [1, 1, 0, 1],
                [1, 0, 1, 1],
                [1, 0, 0, 0],
                [0, 1, 1, 1],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            n_blocks = len(bits) // 4
            blocks = bits.reshape(n_blocks, 4).T
            encoded = np.dot(G, blocks) % 2
            return encoded.T.flatten()
            
        return bits

    @staticmethod
    def decode_data(rx_bits_hard, code_type, orig_len=0):
        """信道译码 (硬判决)"""
        if code_type == "None" or code_type is None:
            return rx_bits_hard
            
        elif code_type == "Repetition(3,1)":
            valid_len = (len(rx_bits_hard) // 3) * 3
            rx_trunc = rx_bits_hard[:valid_len]
            if len(rx_trunc) == 0: return np.array([], dtype=int)
            reshaped = rx_trunc.reshape(-1, 3)
            sums = np.sum(reshaped, axis=1)
            decoded = (sums >= 2).astype(int)
            return decoded
            
        elif code_type == "Hamming(7,4)":
            valid_len = (len(rx_bits_hard) // 7) * 7
            rx_trunc = rx_bits_hard[:valid_len]
            if len(rx_trunc) == 0: return np.array([], dtype=int)
            
            # 使用查表法 (最小汉明距离) 译码
            # 生成所有有效码字
            G = np.array([
                [1, 1, 0, 1],
                [1, 0, 1, 1],
                [1, 0, 0, 0],
                [0, 1, 1, 1],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            
            data_options = []
            codes = []
            for i in range(16):
                d = np.array([int(x) for x in format(i, '04b')])
                data_options.append(d)
                c = np.dot(G, d.reshape(4,1)) % 2
                codes.append(c.flatten())
                
            n_blocks = len(rx_trunc) // 7
            blocks = rx_trunc.reshape(n_blocks, 7).T # 7 x N
            decoded_bits = []
            
            for i in range(n_blocks):
                r_block = blocks[:, i]
                best_dist = 999
                best_idx = 0
                for idx, c in enumerate(codes):
                    dist = np.sum(r_block != c)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = idx
                decoded_bits.extend(data_options[best_idx])
                
            return np.array(decoded_bits)

        return rx_bits_hard

    # --- 调制模块 ---
    @staticmethod
    def modulate(bits, mod_type):
        if mod_type == "BPSK":
            return (2 * bits - 1).astype(complex)
        elif mod_type == "QPSK":
            if len(bits) % 2 != 0: bits = np.append(bits, 0)
            i = 2 * bits[0::2] - 1
            q = 2 * bits[1::2] - 1
            return (i + 1j * q) / np.sqrt(2)
        return (2 * bits - 1).astype(complex)

    # --- 信道模块 ---
    @staticmethod
    def channel_awgn(symbols, snr_db):
        if len(symbols) == 0: return symbols
        sig_power = np.mean(np.abs(symbols)**2)
        if sig_power == 0: sig_power = 1.0
        
        snr_linear = 10**(snr_db / 10.0)
        noise_power = sig_power / snr_linear
        
        noise = (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols))) \
                * np.sqrt(noise_power / 2)
        return symbols + noise

    # --- 解调模块 ---
    @staticmethod
    def demodulate(rx_symbols, mod_type):
        if mod_type == "BPSK":
            return (np.real(rx_symbols) > 0).astype(int)
        elif mod_type == "QPSK":
            bits = np.zeros(len(rx_symbols) * 2, dtype=int)
            bits[0::2] = (np.real(rx_symbols) > 0).astype(int)
            bits[1::2] = (np.imag(rx_symbols) > 0).astype(int)
            return bits
        return (np.real(rx_symbols) > 0).astype(int)
'''

# --- LEVELS ---
levels_code = r'''class LevelManager:
    def __init__(self):
        self.levels = [
            {
                "id": 1,
                "title": "第一次接触",
                "phase": "Part I: 地球联合",
                "mission_text": "任务：建立基础连接，验证 BPSK。\n目标：BER = 0 (无误码)",
                "message": "HELLO_EARTH",
                "message_desc": "[握手信号]",
                "snr_db": 100, 
                "available_mods": ["BPSK"],
                "available_codes": ["None"], 
                "target_ber": 0.0,
                "reward": "解锁 QPSK",
                "source_name": "Camp Alpha", "dest_name": "River Valley",
                "source_pos": (150, 600), "dest_pos": (600, 500), "curve_control": (300, 400)
            },
            {
                "id": 2,
                "title": "跨洋电报",
                "phase": "Part I: 地球联合",
                "mission_text": "任务：跨洋电缆衰减。\n提示：尝试更高速度的 QPSK。",
                "message": "ATLANTIC_LINK",
                "message_desc": "[跨洋链路]",
                "snr_db": 10,
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None"],
                "target_ber": 0.05,
                "reward": "解锁信道编码: 重复码",
                "source_name": "London", "dest_name": "New York",
                "source_pos": (800, 150), "dest_pos": (200, 300), "curve_control": (500, 400)
            },
             {
                "id": 3,
                "title": "战火中的和平",
                "phase": "Part I: 地球联合",
                "mission_text": "剧情：战场干扰严重 (SNR=3dB)。\n必须使用【重复码】来纠正错误！",
                "message": "CEASE_FIRE",
                "message_desc": "[停火指令]",
                "snr_db": 3, 
                "available_mods": ["BPSK"],
                "available_codes": ["None", "Repetition(3,1)"], 
                "target_ber": 0.0,
                "reward": "解锁编码: 汉明码 (Hamming 7,4)",
                "source_name": "UN HQ", "dest_name": "Frontline",
                "source_pos": (200, 200), "dest_pos": (700, 600), "curve_control": (250, 500)
            },
            {
                "id": 4,
                "title": "全球神经网络",
                "phase": "Part I: 地球联合",
                "mission_text": "剧情：网络同步。\n挑战：QPSK + 汉明码 的组合。",
                "message": "NET_SYNC",
                "message_desc": "[网络同步]",
                "snr_db": 7, 
                "available_mods": ["BPSK", "QPSK"], 
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.005,
                "reward": "解锁：深空天线",
                "source_name": "Tokyo", "dest_name": "Sao Paulo",
                "source_pos": (750, 200), "dest_pos": (150, 650), "curve_control": (450, 450)
            },
            {
                "id": 5,
                "title": "联合政府",
                "phase": "Part I: 地球联合",
                "mission_text": "剧情：宪法签署，必须准确。\n组合使用最佳策略。",
                "message": "UNITED_2050",
                "message_desc": "[宪法签署]",
                "snr_db": 8, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Hamming(7,4)"],
                "target_ber": 0.0,
                "reward": "进入太空时代 Phase II",
                "source_name": "Geneva", "dest_name": "Broadcast",
                "source_pos": (450, 350), "dest_pos": (450, 150), "curve_control": (200, 250)
            },
            {
                "id": 6,
                "title": "月球背面",
                "phase": "Part II: 星辰大海",
                "mission_text": "剧情：宇宙噪声 (SNR=-2dB)。\n极其恶劣的环境。",
                "message": "LUNAR_BASE",
                "message_desc": "[基地信号]",
                "snr_db": -2, 
                "available_mods": ["BPSK"],
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.08,
                "reward": "深空阵列",
                "source_name": "Moon", "dest_name": "Earth",
                "source_pos": (750, 100), "dest_pos": (150, 500), "curve_control": (600, 300)
            }, 
             {
                "id": 7,
                "title": "旅行者号",
                "phase": "Part II: 星辰大海",
                "mission_text": "剧情：飞出太阳系，SNR -5dB。\n只有最强的编码能存活。",
                "message": "VOYAGER",
                "message_desc": "[离别]",
                "snr_db": -5, 
                "available_mods": ["BPSK"],
                "available_codes": ["Repetition(3,1)"],
                "target_ber": 0.15,
                "reward": "通关剧情演示",
                "source_name": "Voyager", "dest_name": "Earth",
                "source_pos": (100, 200), "dest_pos": (800, 500), "curve_control": (450, 300)
            }
        ]
        self.current_level_idx = 0

    def get_current_level(self):
        if self.current_level_idx < len(self.levels):
            return self.levels[self.current_level_idx]
        return None

    def next_level(self):
        if self.current_level_idx < len(self.levels) - 1:
            self.current_level_idx += 1
            return True
        return False
'''

# --- MAIN ---
main_code = r'''import pygame
import sys
import numpy as np
import matplotlib.font_manager
from dsp_engine import DSPEngine as dsp
from levels import LevelManager

# --- 初始化 ---
pygame.init()
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Signal Flow Protocol - 通信链路模拟")
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
    available_fonts = set(f.name for f in matplotlib.font_manager.fontManager.ttflist)
    preferred_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
    for f in preferred_fonts:
        if f in available_fonts: return f
    return None 

FONT_NAME = get_font_name()
try:
    font = pygame.font.SysFont(FONT_NAME, 20)
    header_font = pygame.font.SysFont(FONT_NAME, 30)
    label_font = pygame.font.SysFont(FONT_NAME, 16)
except:
    font = pygame.font.SysFont(None, 24)
    header_font = pygame.font.SysFont(None, 36)
    label_font = pygame.font.SysFont(None, 18)

STATE_START_SCREEN = 0
STATE_PLAYING = 1
current_state = STATE_START_SCREEN
level_mgr = LevelManager()

# --- 绘图工具 ---
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

def draw_constellation(surface, symbols, cx, cy, scale=60):
    pygame.draw.line(surface, (50, 50, 50), (cx - 100, cy), (cx + 100, cy), 1)
    pygame.draw.line(surface, (50, 50, 50), (cx, cy - 100), (cx, cy + 100), 1)
    
    max_dots = 400
    step = max(1, len(symbols) // max_dots)
    for s in symbols[::step]:
        x = cx + np.real(s) * scale
        y = cy - np.imag(s) * scale
        if cx-130 < x < cx+130 and cy-90 < y < cy+90:
            pygame.draw.circle(surface, ACCENT_COLOR, (int(x), int(y)), 2)

# --- Button ---
class Button:
    def __init__(self, x, y, w, h, text, callback, color=(60, 60, 70), hover_color=(80, 80, 90)):
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
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1 and self.callback:
                self.callback()

def draw_start_screen(surface, btn):
    surface.fill(BG_COLOR)
    title = header_font.render("SIGNAL FLOW PROTOCOL", True, ACCENT_COLOR)
    sub = font.render("A Comm Engineering Strategy Game", True, (150, 150, 150))
    mx = WINDOW_WIDTH // 2
    surface.blit(title, (mx - title.get_width()//2, 250))
    surface.blit(sub, (mx - sub.get_width()//2, 300))
    btn.draw(surface)

# --- APP ---
def main():
    global current_state
    
    current_mod = "BPSK"
    current_code = "None"
    sim_result = None
    level_complete = False
    
    is_animating = False
    anim_progress = 0.0
    
    ui_mod_rects = []
    ui_code_rects = []

    def cb_start_game():
        nonlocal current_state
        current_state = STATE_PLAYING

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

    def cb_run_sim():
        nonlocal is_animating, anim_progress, sim_result
        if level_complete: return 
        is_animating = True
        anim_progress = 0.0
        sim_result = None 

    def finish_sim():
        nonlocal sim_result, level_complete
        level = level_mgr.get_current_level()
        
        raw_bits = dsp.str_to_bits(level['message'])
        enc_bits = dsp.encode_data(raw_bits, current_code)
        tx_syms = dsp.modulate(enc_bits, current_mod)
        rx_syms = dsp.channel_awgn(tx_syms, level['snr_db'])
        demod_bits = dsp.demodulate(rx_syms, current_mod)
        dec_bits = dsp.decode_data(demod_bits, current_code, len(raw_bits))
        
        # 截断回原始长度
        L = len(raw_bits)
        if len(dec_bits) > L: dec_bits = dec_bits[:L]
        elif len(dec_bits) < L: dec_bits = np.pad(dec_bits, (0, L - len(dec_bits)), 'constant')
        
        rx_msg = dsp.bits_to_str(dec_bits)
        ber = dsp.calculate_ber(raw_bits, dec_bits)
        
        passed = (ber <= level['target_ber'] + 1e-6)
        if passed: level_complete = True
        
        sim_result = {
            "rx_syms": rx_syms,
            "rx_msg": rx_msg,
            "ber": ber,
            "success": passed
        }

    def cb_next_level():
        nonlocal level_complete, sim_result, current_mod, current_code, is_animating
        if level_complete:
            if level_mgr.next_level():
                level_complete = False
                sim_result = None
                is_animating = False
                lvl = level_mgr.get_current_level()
                current_mod = lvl['available_mods'][0]
                current_code = lvl.get('available_codes', ["None"])[0]
            else:
                current_state = STATE_START_SCREEN
                level_mgr.current_level_idx = 0
                level_complete = False
                sim_result = None

    btn_start = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 50, 200, 60, "START STORY", cb_start_game, (0, 100, 150))
    btn_tx = Button(920, 660, 260, 50, "TX SIGNAL", cb_run_sim, (40, 120, 60))
    btn_next = Button(920, 730, 260, 50, "NEXT MISSION >>", cb_next_level, (80, 80, 180))

    while True:
        level = level_mgr.get_current_level()
        if not level: break
        
        if current_mod not in level['available_mods']: current_mod = level['available_mods'][0]
        if current_code not in level.get('available_codes', ["None"]): current_code = "None"

        if current_state == STATE_PLAYING and is_animating:
            anim_progress += 0.02
            if anim_progress >= 1.0:
                anim_progress = 1.0
                is_animating = False
                finish_sim()

        # Events
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if current_state == STATE_START_SCREEN:
                btn_start.handle_event(e)
            
            elif current_state == STATE_PLAYING:
                if not is_animating:
                    btn_tx.handle_event(e)
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = e.pos
                        for rect, m in ui_mod_rects: 
                            if rect.collidepoint((mx, my)): set_mod(m)
                        for rect, c in ui_code_rects:
                            if rect.collidepoint((mx, my)): set_code(c)
                if level_complete:
                    btn_next.handle_event(e)

        # Draw
        if current_state == STATE_START_SCREEN:
            draw_start_screen(screen, btn_start)
        elif current_state == STATE_PLAYING:
            ui_mod_rects.clear(); ui_code_rects.clear()
            screen.fill(BG_COLOR)
            
            # Map
            pygame.draw.rect(screen, MAP_BG_COLOR, (0, 80, 900, 800))
            for x in range(0, 900, 50): pygame.draw.line(screen, (25,30,40), (x,80), (x,WINDOW_HEIGHT))
            for y in range(80, WINDOW_HEIGHT, 50): pygame.draw.line(screen, (25,30,40), (0,y), (900,y))
            
            p0, p1, p2 = level['source_pos'], level['curve_control'], level['dest_pos']
            draw_map_connection(screen, p0, p1, p2, anim_progress, is_animating)
            draw_node(screen, p0, level['source_name'], False)
            draw_node(screen, p2, level['dest_name'], True)
            
            if level['snr_db'] < 10:
                for _ in range(50):
                     pygame.draw.circle(screen, (40,50,60), (np.random.randint(0,900), np.random.randint(80,800)), 1)
            
            # Header
            pygame.draw.rect(screen, PANEL_COLOR, (0,0,WINDOW_WIDTH,80))
            screen.blit(header_font.render(f"{level['phase']} : {level['title']}", True, ACCENT_COLOR), (20,15))
            screen.blit(font.render(f"Target BER < {level['target_ber']} | SNR: {level['snr_db']}dB", True, (150,150,150)), (20,50))
            
            # HUD Background
            bx = 900
            pygame.draw.rect(screen, (25,25,30), (bx, 80, 300, 720))
            pygame.draw.line(screen, ACCENT_COLOR, (bx, 80), (bx, 800), 2)
            
            # Constellation
            cy = 120
            pygame.draw.rect(screen, (0,0,0), (bx+10, cy, 280, 200), border_radius=5)
            screen.blit(label_font.render("RX CONSTELLATION", True, ACCENT_COLOR), (bx+15, 90))
            if sim_result:
                draw_constellation(screen, sim_result['rx_syms'], bx+150, cy+100, 60)
            else:
                pygame.draw.line(screen,(50,50,50),(bx+50,cy+100),(bx+250,cy+100))
                
            # UI: Mod
            y = 340
            screen.blit(label_font.render("MODULATION", True, (150,150,150)), (bx+10, y))
            y += 20
            for i,mod in enumerate(level['available_mods']):
                r = pygame.Rect(bx+10+i*135, y, 125, 35)
                ui_mod_rects.append((r,mod))
                col = ACCENT_COLOR if mod == current_mod else (60,60,70)
                pygame.draw.rect(screen, col, r, border_radius=4)
                if mod == current_mod: pygame.draw.rect(screen, (255,255,255), r, 2, border_radius=4)
                txt = font.render(mod, True, (255,255,255))
                screen.blit(txt, (r.centerx-txt.get_width()//2, r.centery-txt.get_height()//2))
            
            # UI: Code
            y += 50
            screen.blit(label_font.render("CODING", True, (150,150,150)), (bx+10, y))
            y += 20
            for i,code in enumerate(level.get('available_codes', ["None"])):
                r = pygame.Rect(bx+10, y+i*40, 260, 35)
                ui_code_rects.append((r,code))
                col = (200,100,50) if code == current_code else (60,60,70)
                pygame.draw.rect(screen, col, r, border_radius=4)
                if code == current_code: pygame.draw.rect(screen, (255,255,255), r, 2, border_radius=4)
                txt = font.render(code, True, (255,255,255))
                screen.blit(txt, (r.centerx-txt.get_width()//2, r.centery-txt.get_height()//2))

            # Result
            y = 550
            if sim_result:
                s_txt = "SUCCESS" if sim_result['success'] else "FAILED"
                color = SUCCESS_COLOR if sim_result['success'] else ERROR_COLOR
                screen.blit(header_font.render(s_txt, True, color), (bx+10, y))
                screen.blit(font.render(f"BER: {sim_result['ber']:.5f}", True, TEXT_COLOR), (bx+10, y+30))
                screen.blit(font.render(f"Data: {sim_result['rx_msg'][:12]}...", True, (100,200,250)), (bx+10, y+55))
            
            # Task Card
            c_rect = pygame.Rect(20, 100, 380, 150)
            pygame.draw.rect(screen, (30,35,45,230), c_rect, border_radius=8)
            pygame.draw.rect(screen, (80,100,120), c_rect, 1, border_radius=8)
            screen.blit(label_font.render(f"Msg: {level['message_desc']}", True, (255,200,50)), (30, 110))
            y_off = 135
            for line in level['mission_text'].split('\n'):
                screen.blit(font.render(line, True, TEXT_COLOR), (30, y_off))
                y_off += 20

            if not is_animating: btn_tx.draw(screen)
            if level_complete: btn_next.draw(screen)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
'''

with open(r'e:\\heckson\\signal_flow_game\\dsp_engine.py', 'w', encoding='utf-8') as f:
    f.write(dsp_code)
    
with open(r'e:\\heckson\\signal_flow_game\\levels.py', 'w', encoding='utf-8') as f:
    f.write(levels_code)
    
with open(r'e:\\heckson\\signal_flow_game\\main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

print("Files updated successfully.")
