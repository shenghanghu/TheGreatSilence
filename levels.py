
class LevelManager:
    def __init__(self):
        self.levels = [
            # --- 阶段一新增：第一次握手（简化入门关）---
            {
                "id": 1,
                "title": "第一次握手",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "2050年，“大静默”事件席卷全球。\n作为【地球联合 (UEG)】幸存的首席通信工程师，你站在 Base Zero 的控制台前。\n今天，备用天线阵列终于充能完毕。先完成一次最简单的握手：向 Sat-1 发送唤醒指令。",
                "mission_info": "目标：向 Sat-1 发送初始化指令 \"EARTH_INIT\"\n环境：信道状况良好，信噪比已提高。\n操作：选择 BPSK 调制，点击发送即可。",
                "mission_text": "任务：发送初始化指令至 Sat-1。\n当前信道状况：良好。\n只需选择 BPSK 并发送。",
                "message": "EARTH_INIT",
                "message_desc": "[系统初始化]",
                "snr_db": 10,
                "available_mods": ["BPSK"],
                "available_codes": ["None"],
                "target_ber": 0.05,
                "star_thresholds": {"one_star": 0.05, "two_star": 0.02, "three_star": 0.01},
                "tutorial_steps": [
                    {"highlight": "path", "text": "点击绿色节点，再点击红色节点以建立通信链路"},
                    {"highlight": "modulation_panel", "text": "点击选择 BPSK"},
                    {"highlight": "send_button", "text": "点击发送"},
                    {"highlight": "ber_display", "text": "误码率 < 目标即成功"}
                ],
                "nodes": [
                    {"name": "Base Zero", "pos": (150, 600), "origin_pos": (150, 600), "type": "src"},
                    {"name": "Sat-1", "pos": (600, 500), "origin_pos": (600, 500), "type": "dest"}
                ],
                "snr_matrix": [[0, 10], [10, 0]],
                "reward": "解锁下一任务：加上保险"
            },
            # --- 原关卡1 → 关卡2：加上保险 ---
            {
                "id": 2,
                "title": "加上保险",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "上次成功了，但信号质量下降了。\n近地轨道上的 Sat-1 已响应，但信道噪声比预想中更大。\n试试用编码技术来提高可靠性，再次发送初始化指令。",
                "mission_info": "目标：向 Sat-1 发送初始化指令 \"EARTH_INIT\"\n挑战：设备老化严重，发射功率受限。\n建议：利用 BPSK 调制，并启用重复码 (Repetition Code) 作为双重保险。",
                "mission_text": "任务：发送初始化指令至 Sat-1。\n当前信道状况：有噪声。\n建议策略：启用重复码 (Repetition(3,1)) 增强数据防护。",
                "message": "EARTH_INIT",
                "message_desc": "[系统初始化]",
                "snr_db": 5,
                "available_mods": ["BPSK"],
                "available_codes": ["None", "Repetition(3,1)"],
                "target_ber": 0.01,
                "star_thresholds": {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001},
                "reward": "解调模块固件升级：获得 QPSK (正交相移键控) 支持",
                # "educational_images": ... # Removed, using tutorial_slides instead for better flow
                "tutorial_slides": [
                    {
                        "title": "你需要的: 信噪比 (SNR)",
                        "image": "picture/SNR.jpg",
                        "text": "想象你在喧闹的集市里和朋友说话。信噪比就是你朋友的声音和背景吵闹声的比率。如果声音太小，你就会听不清。在通信中，信号就是我们要听的声音，噪声就是干扰。信噪比越高，信号就越清晰。我们用分贝（dB）来衡量它，每提高一点，信号的穿透力就会更强，通信质量也更稳定。"
                    },
                    {
                        "title": "你得到的: 误码率 (BER)",
                        "image": "picture/BER.png",
                        "text": "如果你在一个词里读错了一个字，那就是误码。误码率是传错的份数占总数的比例。比如传了100个字母，错了1个，误码率就是1%。在复杂的环境中，受电磁波干扰，数据很容易“变样”。我们的工程师目标就是通过各种数学魔术，将误码率降到极低，确保指令能被电脑百分之百正确理解，不出一丝差错。"
                    },
                    {
                        "title": "你拥有的: BPSK",
                        "image": "picture/BPSK.png",
                        "text": "这是最憨厚、最稳健的通信方式。就像用手电筒发信号：长闪代表1，短闪代表0。它每次只传1位信息，虽然速度慢，但抗干扰能力极强。即便在暴雨或强干扰的环境下，它也能保证信号被准确接收。它是通讯世界的“指南针”，在所有高科技手段失效时，我们依然可以依靠这种最基础的方式重连世界。"
                    }
                ],
                "nodes": [
                    {"name": "Base Zero", "pos": (150, 600), "origin_pos": (150, 600), "type": "src"},
                    {"name": "Sat-1", "pos": (600, 500), "origin_pos": (600, 500), "type": "dest"}
                ],
                "snr_matrix": [[0, 5], [5, 0]],
                "tech_unlock_info": {
                    "title": "技术解锁: QPSK (正交相移键控)",
                    "image": "picture/QPSK.png",
                    "intro": "既然BPSK一次只能传1位，我们能不能让它快一倍？QPSK就像红绿灯不仅有红绿，还有黄蓝四个颜色。利用信号波形的四个不同旋转角度，它每次闪烁能携带2位信息。这意味着带宽虽然没变，速度却直接翻倍。它就像是把单车道改成了双车道，虽然对司机的技术要求更高，但极大地提升了通行效率。",
                    "specs": "【技术规格】\n- 星座点数: 4 (00, 01, 10, 11)\n- 频带利用率: 2 bits/symbol (BPSK的两倍)\n- 代价: 符号间距离变小，更容易受噪声干扰。"
                }
            },
            {
                "id": 3,
                "title": "跨洋回响",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "近地轨道链路已恢复，但这就够了吗？不。\n大西洋海底的旧光缆正在发出微弱的幽灵脉冲，那里封存着战前的关键气象数据。\n伦敦节点已经沉默了整整五年。我们需要建立一条横跨北大西洋的高速链路来唤醒它。\n上级批准了 QPSK 技术的实验性使用权限。我们需要速度，但越快的速度意味着越脆弱的抗干扰能力——就像在暴风雨中走钢丝。",
                "mission_info": "目标：建立伦敦与纽约之间的高速数据链路\n挑战：传输距离大幅增加，信号在跨洋过程中会经历严重的路径损耗。\n提示：QPSK 速率翻倍，但如果不加保护，误码率将不堪设想。",
                "mission_text": "任务：建立跨洋高速链路。\n必须使用 QPSK 提升速率。\n如果在长距离传输中出现误码，请尝试组合编码技术。",
                "message": "ATLANTIC_LINK_ESTABLISHED",
                "message_desc": "[跨洋握手]",
                "snr_db": 1, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)"],
                "target_ber": 0.01,
                "star_thresholds": {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001},
                "reward": "信道编码升级：获得 Hamming(7,4) 纠错码",
                "nodes": [
                    {"name": "London", "pos": (200, 300), "origin_pos": (200, 300), "type": "src"},
                    {"name": "New York", "pos": (800, 150), "origin_pos": (800, 150), "type": "dest"}
                ],
                "snr_matrix": [[0, 1], [1, 0]],
                "tech_unlock_info": {
                    "title": "技术解锁: Hamming Code (汉明码 7,4)",
                    "image": "picture/Hanming.jpg",
                    "intro": "这是数据的“自愈魔法”。想象你寄信时，每写4个字就附带3个特殊的校验字。如果路上信件被雨水打湿，模糊了一处，收件人通过这3个校验字就能算出那个模糊的字原本是什么并直接写上去。它能自动纠正1位错误并识别更多错误。它是数字时代的保险丝，确保了在长距离传输中，即便遇到小磕小碰，数据依然能完整如初。",
                    "specs": "【技术规格】\n- 码率: R = 4/7 ≈ 0.57\n- 纠错能力: 能够自动纠正 1 位错误\n- 代价: 增加了 75% 的数据冗余，但在高误码环境下这是值得的。"
                }
            },
            {
                "id": 4,
                "title": "辐射云",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "数据链路把世界重新连在了一起，但战争的阴影尚未散去。\n我们需要穿越一片高辐射的旧战区，向位于沙漠中心的自动工厂发送蓝图文件。那里有辐射尘暴，那里的电磁环境混乱得就像一锅煮沸的粥。\n普通的信号进去，出来的只有乱码。我们需要更聪明的校验机制。",
                "mission_info": "目标：穿透高噪声辐射区传输数据\n挑战：极低的信噪比 (SNR)，随机误码频繁爆发。\n提示：Repetition 码太慢，试试 Hamming(7,4) 能否在保证一定速度的同时维持通讯。",
                "mission_text": "任务：穿越辐射云传输工厂指令。\n警告：检测到强干扰。\n提示：Hamming(7,4) 可以纠正单比特错误，非常适合这种零星干扰。",
                "message": "FACTORY_STARTUP_SEQ",
                "message_desc": "[工厂启动]",
                "snr_db": 1, 
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Repetition(3,1)", "Hamming(7,4)"],
                "target_ber": 0.01,
                "star_thresholds": {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001},
                "reward": "网络拓扑数据更新：获得中继节点 (Relay) 权限",
                "nodes": [
                    {"name": "Outpost A", "pos": (100, 100), "origin_pos": (100, 100), "type": "src"},
                    {"name": "Factory", "pos": (900, 700), "origin_pos": (900, 700), "type": "dest"}
                ],
                "snr_matrix": [[0, 1], [1, 0]],
                "tech_unlock_info": {
                    "title": "技术解锁: 中继节点 (Relay Node)",
                    "image": "picture/中继节点.png",
                    "intro": "由于地球是圆的，或者会有大山挡住去路，无线电波很难走直线。中继节点就像是信号的“接力员”：它站在中间，把快要消失的微弱信号接住，清理掉里面的噪音干扰，然后重新注入能量，全力发射到下一站。这不仅延长了通信距离，还能绕过障碍物。在废土世界中，布置合理的中继网络是重新连接散落聚落的唯一出路。",
                    "specs": "【技术规格】\n- 功能: Decode-and-Forward (解码转发) 或 Amplify-and-Forward (放大转发)\n- 优势: 将长距离高损耗链路分割为多段短距离低损耗链路。"
                }
            },
            {
                "id": 5,
                "title": "中继网络",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "工厂启动了，但我们的野心不止于此。为了覆盖整个由城市废墟构成的迷宫，单点对单点的传输已经不够用了。\n我们需要建立一个中继网络，绕过那些高耸的屏蔽墙（摩天大楼的残骸）。\n这是对你拓扑规划能力的考验。选错路径，信号就会死在半路上。",
                "mission_info": "目标：利用中继节点绕过障碍，建立多跳链路\n挑战：直接路径被严重阻挡（高损耗）。\n机制：点击中继节点（黄色）将其加入路径。路径越短并不总是越好，要看每一跳的质量。",
                "mission_text": "任务：通过中继节点连接目标。\n操作：左键点击节点规划路径，右键清除。\n提示：寻找信噪比最高的路径组合。",
                "message": "NETWORK_EXPANSION_PACK",
                "message_desc": "[网络扩展]",
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["None", "Hamming(7,4)"],
                "target_ber": 0.05,
                "star_thresholds": {"one_star": 0.05, "two_star": 0.02, "three_star": 0.01},
                "reward": "极化码原型机：获得 Polar Code (SC Decoder)",
                "satellite_deployment": {
                    "enabled": True,
                    "budget": 1000,
                    "position_range": {"x": (220, 760), "y": (120, 700)},
                    "reference_pos": (100, 400),
                    "cost_per_distance": 1.8,
                    "max_satellites": 2,
                },
                # 节点索引: 0:HQ, 1:Relay Alpha, 2:Relay Beta, 3:Ruins
                "snr_matrix": [
                    # To:  HQ    Alpha  Beta   Ruins
                    [      0,    15,    -10,   -20  ], # From HQ (0)
                    [      15,   0,     -8,    12   ], # From Relay Alpha (1)
                    [      -10,  -8,     0,     -5   ], # From Relay Beta (2)
                    [      -20,  12,    -5,     0    ]  # From Ruins (3)
                ],
                "nodes": [
                    {"name": "HQ", "pos": (100, 400), "origin_pos": (100, 400), "type": "src"},
                    {"name": "Relay Alpha", "pos": (400, 200), "origin_pos": (400, 200), "type": "relay"},
                    {"name": "Relay Beta", "pos": (400, 600), "origin_pos": (400, 600), "type": "relay"},
                    {"name": "Ruins (Dest)", "pos": (800, 400), "origin_pos": (800, 400), "type": "dest"}
                ],
                "tech_unlock_info": {
                    "title": "技术解锁: Polar Codes (极化码)",
                    "image": "picture/polarcode.png",
                    "intro": "这是由数学天才阿利坎教授发现的“信道奇迹”。他证明了通过一套精妙的算法，可以将原本杂乱的通信路径分化。就像把一条充满碎石的路变成两条：一条是彻底清理干净的“高速公路”，另一条则是堆满垃圾的“死路”。我们专门在高速公路上传输核心数据。这是目前人类在数学上最接近“通信极限”的方案，也是5G的核心基石。",
                    "specs": "【技术规格】\n- 核心原理: 信道极化 (Channel Polarization)\n- 解码器: SC (Successive Cancellation) - 这里的入门级算法。\n- 优势: 理论上能达到香农极限的编码方案。"
                }
            },
            {
                "id": 6,
                "title": "极化初现",
                "phase": "第一章: 尘埃与回响",
                "story_intro": "这是地面通信的最后一块拼图。我们要在极度恶劣的雷雨天气中，向平流层飞艇发送控制流。\n传统的 Hamming 码已经力不从心，误码率居高不下。\n是时候祭出我们的新式武器——Polar Code 了。感受数学的力量吧，看它如何从混乱中提取秩序。",
                "mission_info": "目标：在高噪声环境下测试 Polar 码性能\n挑战：信噪比极低，此时传统编码几乎失效。\n提示：Polar Code 配合 SC 解码器，能在这种恶劣环境下创造奇迹。",
                "mission_text": "任务：在雷雨干扰下维持飞艇链路。\n要求：使用 Polar Code。\n观察：对比 Hamming 码，看 Polar 码如何在低 SNR 下保持低误码率。",
                "message": "STRATOSPHERE_UPLINK",
                "message_desc": "[飞艇上行]",
                "available_mods": ["BPSK", "QPSK"], 
                "available_codes": ["Hamming(7,4)", "Polar(16,8)"], 
                "target_ber": 0.005,
                "star_thresholds": {"one_star": 0.005, "two_star": 0.002, "three_star": 0.001},
                # 节点索引: 0:Ground, 1:Weather, 2:Thunder, 3:Airship
                "snr_matrix": [
                    # To:  Ground Vane   Cloud  Airship
                    [      0,     4,    -5,    -20   ], # From Ground Station (0)
                    [      4,    0,     0,     3     ], # From Weather Vane (1)
                    [      -5,    0,     0,     -5    ], # From Thunder Cloud (2)
                    [      -20,   3,     -5,    0     ]  # From Airship (3)
                ],
                "nodes": [
                    {"name": "Ground Station", "pos": (100, 700), "origin_pos": (100, 700), "type": "src"},
                    {"name": "Weather Vane", "pos": (300, 500), "origin_pos": (300, 500), "type": "relay"},
                    {"name": "Thunder Cloud", "pos": (600, 300), "origin_pos": (600, 300), "type": "relay"},
                    {"name": "Airship", "pos": (800, 100), "origin_pos": (800, 100), "type": "dest"}
                ],
                "tech_unlock_info": {
                    "title": "技术解锁: BP Decoder (置信传播)",
                    "intro": "传统的解码器比较“死脑筋”，看到什么就信什么。而BP解码器充满“智慧”。它在解密时，会让每一个数据位和其他位反复交流、相互推演，就像侦探们在讨论案情：“我觉得这位应该是1，你觉得呢？”通过多次迭代循环，它们会逐渐达成共识。这种群策群力的算法，极大地提升了在超高噪声环境下找回原始数据真相的成功率。",
                    "specs": "【技术规格】\n- 算法: 迭代消息传递 (Iterative Message Passing)\n- 优势: 并行度高，潜能比 SC 更大，适合更长的码字。"
                }
            },
            # --- Phase II: 星之方舟 (Ark of Stars) ---
            {
                "id": 7,
                "title": "轨道突围",
                "phase": "第二章: 星之方舟",
                "story_intro": "地面的事情已经解决。现在，目光转向星空。\n'Ark' 计划启动——我们要向太阳系边缘发射深空探测器，寻找新家园的线索。\n但首先，我们必须突破布满太空垃圾的近地轨道封锁线。这里是卫星的坟场，信号的禁区。\n你需要在这里重新校准所有的通信协议。",
                "mission_info": "目标：建立地月通信链路\n挑战：动态环境！卫星和垃圾都在高速移动。\n机制：节点位置随时间变化，多普勒效应和遮挡开始显现（模拟）。\n新技术：尝试使用 BP 解码器提升接收增益。",
                "mission_text": "任务：建立地月稳定链路。\n环境：高动态轨道。\n建议：使用 Polar 码配合 BP 解码器来应对快速变化的信道条件。",
                "message": "在这个被碎片包裹的星球上空，每一块漂浮的残骸都是旧时代盲目扩张的墓碑。它们像钢铁囚笼一样锁住了天空，也几乎窒息了我们的未来。但今天，我们将撕开这道帷幕。这不仅仅是一次突围，而是为了延续文明火种的最后搏杀。方舟号引擎已预热，目标锁定月球网关。无论前方是深渊还是星海，我们都将一往无前，为了寻找那个尚在梦中的应许之地，为了让后人不再仰望这片灰暗的天空。",
                "message_desc": "[地月网关]",
                "available_mods": ["BPSK","QPSK"],
                "available_codes": ["Repetition(3,1)", "Polar(256,128)", "Polar(1024,512)"],
                "target_ber": 0.01,
                "star_thresholds": {"one_star": 0.01, "two_star": 0.005, "three_star": 0.001},
                "reward": "物理层大杀器：获得太空激光通讯 (Laser Link) 模组",
                "tutorial_slides": [
                    {
                        "title": "深空挑战: 自由空间路径损耗 (FSPL)",
                        "image": "picture/自由空间路径损耗.png",
                        "text": "在广袤无垠的宇宙真空中，信号虽然没有云层遮挡，但它会像吹大的肥皂泡一样能量扩散。每当你离信号源远一倍，信号的强度就会减弱到原来的四分之一（-6dB）。在跨越地月甚至更远的深空距离时，这种损耗大得惊人。了解并计算这种自然界的物理规律，是我们设计深空探测器时必须面对的第一个数学难题。"
                    }
                ],
                "nodes": [
                    {"name": "Earth Link", "pos": (100, 400), "origin_pos": (100, 400), "type": "src"},      # 0
                    {"name": "Orbital Station", "pos": (300, 400), "origin_pos": (300, 400), "type": "relay"}, # 1
                    {"name": "Debris A", "pos": (400, 300), "origin_pos": (400, 300), "type": "relay"},        # 2
                    {"name": "L1 Point", "pos": (600, 400), "origin_pos": (600, 400), "type": "relay"},        # 3
                    {"name": "Lunar Orbit", "pos": (800, 300), "origin_pos": (800, 300), "type": "relay"},     # 4
                    {"name": "Debris B", "pos": (850, 450), "origin_pos": (850, 450), "type": "relay"},        # 5
                    {"name": "Luna Base", "pos": (950, 400), "origin_pos": (950, 400), "type": "dest"}         # 6
                ],
                "tech_unlock_info": {
                    "title": "技术解锁: Laser Communications (激光通讯)",
                    "image": "picture/laser.png",
                    "intro": "传统的无线电波像大喇叭广播，到处乱跑且带宽有限。激光通讯则是“点对点”的精准投送。它利用频率极高的光波，能携带极其海量的数据——一部高清电影甚至只需几秒就能传完。而且激光方向性极强，抗拦截性非常好。只要你能像狙击手一样瞄准几万公里外的目标，它就是连接星辰大海的终极数据桥梁。",
                    "specs": "【技术规格】\n- 优势: 极高增益，极高带宽，极低被截获率。\n- 劣势: 需要极高精度的瞄准 (PAT: Pointing, Acquisition, and Tracking)，且怕云层遮挡（太空中无此问题）。"
                }
            },
            {
                "id": 8,
                "title": "木星引力",
                "phase": "第二章: 星之方舟",
                "story_intro": "激光通讯模块已上线。我们在木星轨道部署了中继器，利用其巨大的引力弹弓加速探测器。\n但木星强烈的磁暴产生了可怕的背景噪声。这是一场能量与精度的较量。\n启动激光模块，用光束刺穿这层电子迷雾。",
                "mission_info": "目标：在强磁暴干扰下维持通讯\n挑战：超远距离导致信号极度衰减，背景噪声巨大。\n操作：在界面右侧激活 \"Laser Module\"。这会消耗额外能量，但能显著提升 SNR。",
                "mission_text": "任务：点亮木星中继站。\n操作：必须启用 LASER MODULE 才能穿透磁暴。\n提示：激光能提供巨大的 SNR 增益，它是深空通信的唯一解。",
                "message": "木星的大红斑如同一只古老的邪眼，冷冷地审视着我们这些渺小的闯入者。这里的磁场如同狂暴的野兽，不断撕扯着微弱的电波信号。但正是这股毁灭性的力量，将成为我们跳向深空的最好踏板。我们必须在混沌的风暴中心搭建起稳定的激光链路，将方舟号的轨道参数精准注入。这是最后的引力变轨机会，成败在此一举，我们将借巨人之力，飞越太阳系的边界。",
                "message_desc": "[引力弹弓]",
                "tx_power": 70, # 调整：提高发射功率
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)", "Polar(512,256)", "Polar(1024,512)"],
                "target_ber": 0.002,
                "star_thresholds": {"one_star": 0.002, "two_star": 0.001, "three_star": 0.0005},
                "reward": "解码算法终极形态：获得 SCL (Successive Cancellation List) 解码器",
                "nodes": [
                    {"name": "Europa Base", "pos": (100, 600), "origin_pos": (100, 600), "type": "src"},
                    {"name": "Io Relay", "pos": (300, 400), "origin_pos": (300, 400), "type": "relay"},
                    {"name": "Ganymede Relay", "pos": (500, 200), "origin_pos": (500, 200), "type": "relay"},
                    {"name": "Jovian Hub", "pos": (800, 500), "origin_pos": (800, 500), "type": "dest"}
                ],
                "tech_unlock_info": {
                    "title": "技术解锁: SCL Decoder (串行抵消列表)",
                    "intro": "SCL解码器是目前极化码解码的“巅峰形态”。它不再孤注一掷地选择一种判断，而是采用了“平行宇宙”策略。在遇到不确定的比特位时，它会保留多条可能的解码路径，像分身一样齐头并进。直到最后通过校验和，它会从这几条路径中精准识别出那条通往真相的唯一生还路径。它的性能极其强悍，几乎是目前信道编码领域的性能极限。",
                    "specs": "【技术规格】\n- 列表大小 (List Size): L (通常为4, 8, 32)\n- 配合: CA-SCL (CRC-Aided SCL) 性能甚至能超越 Turbo 码和 LDPC 码。"
                }
            },
            {
                "id": 9,
                "title": "碎石带",
                "phase": "第二章: 星之方舟",
                "story_intro": "警告：探测器群正在穿越小行星带。\n这里不仅有随机的物理撞击风险（如果运气不好），更有无数富含金属的小行星在反射和散射信号。\n这是一个动态迷宫。你需要利用 SCL 解码器的强力纠错性能，配合激光的穿透力，在这片混沌中杀出一条血路。\n注意：障碍物会遮挡视线，导致通信中断！选择正确的时机和路径。",
                "mission_info": "目标：穿越小行星带\n挑战：动态遮挡！小行星（灰色块）会切断链路。\n机制：如果视线 (Line of Sight) 被阻挡，SNR 会骤降。预判小行星的运动轨迹！",
                "mission_text": "任务：穿越移动的小行星屏障。\n警告：LOS (视线) 遮挡致命。\n策略：观察小行星周期，选择开阔窗口发射。SCL 解码器能容忍瞬间的信号抖动。",
                "message": "战争的阴云早已散去，但它涂抹在文明脸庞上的灰烬从未被雨水洗净。怨恨、遗憾、悲伤......这些沉重的包袱，终将被辐射尘深深地埋葬在曾经丰饶的沃土之下。现在，我们唯有前进这一条路可走。宇宙虽寂暗无声，却处处潜藏着新生的脉搏。这些信号会携带着我们的心愿飞向更遥远的地平线，如同当年先辈们驶出摇篮那样，即使是微弱的火种，也要在那无尽的黑暗中开拓出新的家园。",
                "message_desc": "[穿越碎石]",
                "tx_power": 70, # 调整：提高发射功率
                "available_mods": ["BPSK","QPSK"],
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)", "Polar(512,256)"],
                "target_ber": 0.002,
                "star_thresholds": {"one_star": 0.0002, "two_star": 0.0001, "three_star": 0.00005},
                "reward": "获得深空探测器控制权",
                "nodes": [
                    {"name": "Mission Control", "pos": (100, 400), "origin_pos": (100, 400), "type": "src"}, # Index 0
                    {"name": "Belt Outpost A", "pos": (400, 200), "origin_pos": (400, 200), "type": "relay"}, # Index 1
                    {"name": "Belt Outpost B", "pos": (400, 600), "origin_pos": (400, 600), "type": "relay"}, # Index 2
                    {"name": "Center Probe", "pos": (600, 400), "origin_pos": (600, 400), "type": "relay"},   # Index 3
                    {"name": "Comet 67P", "pos": (800, 400), "origin_pos": (800, 400), "type": "relay"},      # Index 4
                    {"name": "Deep Space 1", "pos": (1000, 400), "origin_pos": (1000, 400), "type": "dest"}   # Index 5
                ]
                # obstacles list is generated by main.py
            },
            {
                "id": 10,
                "title": "深渊凝视",
                "phase": "第二章: 星之方舟",
                "story_intro": "我们到达了柯伊伯带。这里是太阳系的尽头，光芒微弱得几乎看不见。\n这也是最后的考验。我们要向已经飞出日球层的“旅行者3号”同步最终的星图数据。\n距离极其遥远，信号要在虚空中漂泊数小时。每一个光子都弥足珍贵。\n在这里，只有最顶级的技术组合（Laser + QPSK + Polar-SCL）才能在虚无中点亮一丝火花。",
                "mission_info": "目标：超深空通讯\n挑战：极限距离，极限信噪比。\n终极测试：综合运用你学到的一切。没有容错空间。",
                "mission_text": "任务：链接旅行者3号。\n提示：这是最后的挑战。\n愿原力...愿香农与你同在。",
                "message": "我们终于抵达了柯伊伯带的尽头，这里的太阳已经暗淡得像一颗遥远的星辰。所有的爱恨情仇，在此刻都被宇宙的极寒冻结。半个世纪前，旅行者3号孤身闯入这片永夜，它身上携带着人类最初的好奇与最纯真的善意。现在，建立链接的一刹那，这些数据将不再是孤独的自白，它们化作了我们最后的希望信标，驶向更深的黑暗，去寻找那未必存在、却必须追寻的生机。",
                "message_desc": "[最终同步]",
                "available_mods": ["BPSK","QPSK"],
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)", "Polar(512,256)", "Polar(1024,512)"],
                "target_ber": 0.0002,
                "star_thresholds": {"one_star": 0.0002, "two_star": 0.0001, "three_star": 0.00005},
                "reward": "通关游戏：解锁“无尽模式”与“开发者访谈”",
                "nodes": [
                    {"name": "Unified Array", "pos": (100, 400), "origin_pos": (100, 400), "type": "src"}, # Offset for orbit
                    {"name": "Kuiper Obj A", "pos": (400, 300), "origin_pos": (400, 300), "type": "relay"},
                    {"name": "Kuiper Obj B", "pos": (400, 500), "origin_pos": (400, 500), "type": "relay"},
                    {"name": "Oort Cloud", "pos": (700, 400), "origin_pos": (700, 400), "type": "relay"},
                    {"name": "Deep Space Buoy", "pos": (850, 200), "origin_pos": (850, 200), "type": "relay"},
                    {"name": "The Void", "pos": (980, 400), "origin_pos": (980, 400), "type": "dest"}
                ]
                # obstacles list is generated by main.py
            },
            {
                "id": 11,
                "title": "昆仑",
                "phase": "终章: 归乡",
                "story_intro": "星图已发出，我们的使命完成了。\n但在关闭系统前，还有一个特殊的请求。\n位于月球背面的昆仑基地发来了一条加密消息。\n那不是求救，是一首诗。用最古老的 BPSK 编码，写给地球的情书。\n让我们把这最后的声音，带回家。",
                "mission_info": "目标：回传昆仑基地的消息至地球\n挑战：太阳耀斑正在爆发（动态干扰源）。\n享受这最后一程吧，指挥官。",
                "mission_text": "任务：从月背回传数据。\n干扰：太阳风暴。\n状态：归途。",
                "message": "这里是月球背面静海之下的昆仑基地，我们用最古老的信号向母星致以最后的问候。那些已经随着方舟驶向星辰大海的朋友们，他们的勇气如同这里的黑夜一般永恒。而我们留守在此，看那颗蔚蓝的行星依然在虚空中发光，那是无论走多远都无法割舍的灯塔。当这条消息穿越 raging 的太阳风暴抵达时，请告诉还活着的孩子们：这一刻，人类终于没有了边界，我们回家了。",
                "message_desc": "[回家]",
                "tx_power": 65, # 调整：提高发射功率
                "available_mods": ["BPSK", "QPSK"],
                "available_codes": ["Repetition(3,1)", "Hamming(7,4)", "Polar(512,256)", "Polar(1024,512)"],
                "target_ber": 0.0,
                "star_thresholds": {"one_star": 0.001, "two_star": 0.0001, "three_star": 0.0},
                "reward": "感谢游玩 SIGNAL FLOW PROTOCOL!",
                "nodes": [
                    {"name": "KUNLUN Base", "pos": (950, 100), "origin_pos": (950, 100), "type": "src"}, # 0
                    {"name": "Defense Sat", "pos": (800, 200), "origin_pos": (800, 200), "type": "relay"}, # 1
                    {"name": "Asteroid Base", "pos": (700, 300), "origin_pos": (700, 300), "type": "relay"}, # <NEW SATELLITE>
                    {"name": "Jovian Relay", "pos": (600, 400), "origin_pos": (600, 400), "type": "relay"}, # 2
                    {"name": "Mars Outpost", "pos": (400, 600), "origin_pos": (400, 600), "type": "relay"}, # 3
                    {"name": "Lagrange Sat", "pos": (500, 500), "origin_pos": (500, 500), "type": "relay"}, # <NEW SATELLITE>
                    {"name": "Moon Base", "pos": (200, 500), "origin_pos": (200, 500), "type": "relay"},   # 4
                    {"name": "EARTH", "pos": (80, 700), "origin_pos": (80, 700), "type": "dest"}         # 5
                ]
            }
        ]
        self.current_level_idx = 0 # 从第一关开始

    def get_current_level(self):
        if 0 <= self.current_level_idx < len(self.levels):
            return self.levels[self.current_level_idx]
        return None

    def next_level(self):
        if self.current_level_idx < len(self.levels) - 1:
            self.current_level_idx += 1
            return True
        return False
