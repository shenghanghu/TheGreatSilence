class LevelManager:
    def __init__(self):
        self.levels = [
            # --- Phase I: 地球联合 (Earth Union) ---
            {
                "id": 1,
                "title": "废土重启",
                "phase": "Part I: 地球联合",
                "story_intro": "2050年，旧网络已在战火中焚毁。作为【地球联合】的首席通信官，你的首要任务是重启地表的基础通信链路。\n基地 Zero 的设备依然简陋，周围充满了未知的电磁干扰。\n我们必须先确保第一条指令能够从指挥中心送达已停摆的卫星 Sat-1。",
                "mission_info": "目标：从 Base Zero 发送初始化指令 \"EARTH_INIT\" 至 Sat-1\n条件：误码率 (BER) 低于 1%\n建议：环境噪声已被屏蔽，但设备可能不稳定，尝试使用简单的编码。",
                "mission_text": "任务：发送初始化指令至 Sat-1。\n信道噪声已屏蔽。直接 BPSK 即可。\n请使用【重复码】作为双重保险。",
                "message": "EARTH_INIT",
                "message_desc": "[初始化指令]",
                "snr_db": 5, 
                "available_mods": ["BPSK"],
                "available_codes": ["None", "Repetition(3,1)"], 
                "target_ber": 0.01, 
                "reward": "解调模块升级：获得 QPSK 调制支持",
                "source_name": "Base Zero",
                "dest_name": "Sat-1",
                "source_pos": (150, 600), "dest_pos": (600, 500), "curve_control": (300, 400),
                "tech_unlock_info": {
                    "title": "技术解锁: QPSK (正交相移键控)",
                    "intro": "【科普】\n想象不仅利用光线的明暗（0和1）来传递信号，还要利用光线的颜色。BPSK 就像开关灯，只有两个状态。而 QPSK 就像是一个有四个方向的红绿灯（上下左右），每次闪烁可以传递两个比特的信息。\n这项技术让我们的传输速率直接翻倍，是重建全球高速网络的基石。",
                    "specs": "【技术规格】\n- 全称: Quadrature Phase Shift Keying\n- 星座点数: 4 (00, 01, 10, 11)\n- 频带利用率: 2 bits/symbol (是 BPSK 的两倍)\n- 抗噪性能: 在相同误码率下，与 BPSK 理论性能相当，但对相位噪声更敏感。\n- 优缺点: 速率快，但符号间距离变小，更容易受噪声干扰。"
                }
            },
            {
                "id": 2,
                "title": "跨洋回响",
                "phase": "Part I: 地球联合",
                "story_intro": "卫星链路已恢复，但这就够了吗？不。\n大西洋海底的旧光缆正在发出微弱的信号，那里有战前的关键数据。\n我们需要更高的数据传输速率来唤醒沉睡的伦敦节点。\n上级批准了 QPSK 调制技术的使用权限，但这会降低每个符号的能量距离。",
                "mission_info": "目标：建立伦敦与纽约之间的高速链路\n条件：误码率 (BER) 低于 1%\n提示：QPSK 速率翻倍，但抗噪能力变弱。若误码过高，请配合编码使用。",
                "mission_text": "任务：建立跨洋高速链路。\n使用 QPSK 提升速率。\n如果误码率过高，尝试组合编码技术。",
                "message": "ATLANTIC_LINK_ESTABLISHED",
                "message_desc": "[跨洋链路]",
                "snr_db": 3, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)"],
                "target_ber": 0.01, 
                "reward": "信道编码升级：获得 Hamming(7,4) 纠错码",
                "source_name": "London", "dest_name": "New York",
                "source_pos": (800, 150), "dest_pos": (200, 300), "curve_control": (500, 400),
                "tech_unlock_info": {
                    "title": "技术解锁: Hamming Code (汉明码 7,4)",
                    "intro": "【科普】\n理查德·汉明在 1950 年发明了这项魔法。\n假设你在传输一串数字，每发送 4 个有用的数字，就附赠 3 个像是“校验和”一样的额外数字。这 3 个数字巧妙地包含了前面 4 个数字的逻辑关系。\n如果接收方发现这 7 个数字里有任何 1 个数字出错了，这 3 个校验位就像侦探一样，能精准地指出是哪一位错了，并把它修正过来！",
                    "specs": "【技术规格】\n- 类型: 线性分组码 (Linear Block Code)\n- 码率: R = 4/7 ≈ 0.57\n- 最小距离 (d_min): 3\n- 纠错能力: 能够纠正 1 位错误 (d <= (3-1)/2 = 1)\n- 检错能力: 能够检测 2 位错误\n- 代价: 传输 7 个比特只包含 4 个比特的信息，带宽占用增加 75%。"
                }
            },
             {
                "id": 3,
                "title": "最终停火",
                "phase": "Part I: 地球联合",
                "story_intro": "联合政府成立前夕，边境仍有交火。\n为了拯救前线的士兵，一条“紧急停火”指令必须瞬间传遍战场。\n这一次，信号不仅要快，还要绝对准确。\n工程师为你送来了【汉明码】，这是一种古老但高效的纠错技术。",
                "mission_info": "目标：向战区发送 \"CEASE_FIRE_IMMEDIATELY\"\n条件：误码率 (BER) 低于 0.5%\n技术：对比重复码，汉明码(7,4)能在保持一定速率的同时提供纠错能力。",
                "mission_text": "任务：发送紧急停火指令。\n测试 QPSK + 汉明码 的性能。\n汉明码效率高于重复码，均有纠错能力。",
                "message": "CEASE_FIRE_IMMEDIATELY",
                "message_desc": "[紧急停火]",
                "snr_db": 0.2, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"], 
                "target_ber": 0.005,
                "reward": "发射功率增强：信噪比 +2dB",
                "source_name": "UN HQ", "dest_name": "Frontline",
                "source_pos": (200, 200), "dest_pos": (700, 600), "curve_control": (250, 500)
            },
            {
                "id": 4,
                "title": "全球心跳",
                "phase": "Part I: 地球联合",
                "story_intro": "和平降临，现在是让地球“像一个整体于呼吸”的时候了。\n我们要启动全球神经网络同步。\n东京与圣保罗之间的数据流将决定全球电网的稳定性。\n这是一场关于精准度的终极测试，任何一点噪声都可能导致大停电。",
                "mission_info": "目标：同步全球网络节点\n条件：误码率 (BER) 必须为 0.0 (无误码)\n挑战：寻找当前环境下最佳的 调制+编码 组合。",
                "mission_text": "任务：建立全球同步网络。\n要求绝对精准 (BER=0)。\n寻找最佳配置。",
                "message": "GLOBAL_SYNC_Verified_2026",
                "message_desc": "[网络同步]",
                "snr_db": -2, 
                "available_mods": ["BPSK", "QPSK"], 
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.0,
                "reward": "巨型工程：构建行星发射台",
                "source_name": "Tokyo", "dest_name": "Sao Paulo",
                "source_pos": (750, 200), "dest_pos": (150, 650), "curve_control": (450, 450)
            },
            {
                "id": 5,
                "title": "星际宣言",
                "phase": "Part I: 地球联合",
                "story_intro": "这是历史性的一刻。\n地球联合宪法已签署，我们将向轨道空间站发送这份宣言。\n这不仅是通信，更是人类文明迈向星空的誓词。\n利用我们在地球上获得的所有技术，高声呐喊吧。",
                "mission_info": "目标：向轨道发送 \"HUMANITY_UNITED_FOREVER\"\n条件：误码率 (BER) 必须为 0.0\n环境：信号极佳 (SNR=10dB)，这是地球给我们的最后馈赠。",
                "mission_text": "任务：向轨道广播联合宪法。\n这是我们在地球上的最后一次广播。\n保持完美传输。",
                "message": "HUMANITY_UNITED_FOREVER",
                "message_desc": "[联合广播]",
                "snr_db": -3, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.0,
                "reward": "开启新篇章：Part II 星辰大海",
                "source_name": "Geneva", "dest_name": "Orbit",
                "source_pos": (450, 350), "dest_pos": (450, 150), "curve_control": (200, 250)
            },
            
            # --- Phase II: 星辰大海 ---
            {
                "id": 6,
                "title": "月面静默",
                "phase": "Part II: 星辰大海",
                "story_intro": "我们离开了大气层的庇护。\n月球背面基地 Alpha 正在尝试建立首个深空节点。\n宇宙背景辐射无情地冲刷着微弱的信号，这里的信噪比低得可怕 (-2dB)。\n速度不再重要，只有生存。使用你能找到的最强纠错手段。",
                "mission_info": "目标：建立月球-地球链路\n条件：误码率 (BER) 低于 5%\n挑战：SNR极低 (-2dB)。BPSK是必须的，QPSK几乎无法工作。",
                "mission_text": "任务：建立地月链路。\n宇宙噪声巨大 (SNR=-2dB)。\n必须使用最强的纠错手段。",
                "message": "LUNAR_BASE_ALPHA",
                "message_desc": "[月球首通]",
                "snr_db": -2, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.05,
                "reward": "解锁：深空阵列 (更大接收增益)",
                "source_name": "Moon", "dest_name": "Earth",
                "source_pos": (750, 100), "dest_pos": (150, 500), "curve_control": (600, 300)
            }, 
             {
                "id": 7,
                "title": "最后的告别",
                "phase": "Part II: 星辰大海",
                "story_intro": "旅行者号探测器即将飞出太阳系边缘。\n它的电池即将耗尽，这是它发回地球的最后一句告别。\n信号淹没在无穷无尽的星际噪声中 (-5dB)。\n这是一次跨越半个世纪的握手，请不要让它变成乱码。",
                "mission_info": "目标：接收旅行者号的最后信息\n条件：误码率 (BER) 低于 10%\n终极挑战：在极限物理条件下，提取出那句珍贵的再见。",
                "mission_text": "任务：接收旅行者号离别信号。\n极限噪声 (SNR=-5dB)。\n哪怕一个误码都可能毁掉它。",
                "message": "VOYAGER_GOODBYE",
                "message_desc": "[离别信号]",
                "snr_db": -5, 
                "available_mods": ["BPSK"], 
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.1, 
                "reward": "游戏通关 - 感谢游玩",
                "source_name": "Voyager", "dest_name": "Earth",
                "source_pos": (100, 200), "dest_pos": (800, 500), "curve_control": (450, 300)
            }
        ]
        self.current_levels_code_updated = True # Flag
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
