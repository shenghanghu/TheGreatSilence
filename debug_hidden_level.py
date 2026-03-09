import pygame
import numpy as np
import sys
import math

# 配置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 900
BG_COLOR = (10, 10, 15)
ACCENT_COLOR = (0, 180, 255)
ERROR_COLOR = (230, 80, 80)
SUCCESS_COLOR = (50, 200, 100)
FONT_NAME = "Microsoft YaHei"

# 初始化
pygame.init()
try:
    font = pygame.font.SysFont(FONT_NAME, 20)
    header_font = pygame.font.SysFont(FONT_NAME, 30)
except:
    font = pygame.font.SysFont(None, 24)
    header_font = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Hidden Level Debugger")

# --- 模拟游戏逻辑 ---

# 1. 生成逻辑 (直接复用原有逻辑)
def generate_hidden_level_data():
    rows = 4
    cols = 5
    
    # 规则: 随机选3行，每行1个好卫星
    good_rows = np.random.choice(range(rows), 3, replace=False)
    
    nodes = []
    
    # Source
    nodes.append({"name": "Earth Link", "pos": (700, 700), "type": "src", "status": "normal"})
    
    # Sat Array
    center_x, center_y = 700, 850
    base_radius = 200
    radius_step = 100
    angle_start = -np.pi * 0.8 
    angle_end = -np.pi * 0.2 
    angle_step = (angle_end - angle_start) / (cols - 1)
    
    debug_good_count = 0

    for r in range(rows):
        has_good = r in good_rows
        good_col = -1
        if has_good:
            good_col = np.random.randint(0, cols)
            
        current_radius = base_radius + r * radius_step
        
        for c in range(cols):
            angle = angle_start + c * angle_step
            # Jitter
            jitter_a = np.random.uniform(-0.05, 0.05)
            jitter_r = np.random.uniform(-10, 10)
            
            px = center_x + (current_radius + jitter_r) * np.cos(angle + jitter_a)
            py = center_y + (current_radius + jitter_r) * np.sin(angle + jitter_a)
            
            # Status
            if c == good_col:
                status = "good" 
                debug_good_count += 1
            else:
                status = "damaged"
                
            name = f"Sat-{r+1}-{c+1}"
                
            nodes.append({
                "name": name, 
                "pos": (px, py), 
                "type": "relay", 
                "status": status
            })

    # Dest
    nodes.append({"name": "Array Core", "pos": (700, 100), "type": "dest", "status": "normal"})
    
    return nodes, debug_good_count

# 2. 状态变量
current_nodes = []
path_indices = []
message = "Press SPACE to Regenerate | Click nodes to connect | ENTER to Check"
good_sats_total = 0

# 3. 初始化第一次
current_nodes, good_sats_total = generate_hidden_level_data()

# 4. 辅助函数
def get_node_at_pos(pos):
    for i, n in enumerate(current_nodes):
        nx, ny = n['pos']
        dist = np.hypot(pos[0]-nx, pos[1]-ny)
        if dist < 25: return i
    return None

def check_result():
    global message
    found_good = 0
    found_bad = 0
    
    # path_indices 存的是索引
    # 排除第一个(src)和最后一个(dest)如果仅仅是经过的话，或者看具体逻辑
    # 游戏中是检查路径中的 relay
    
    visited_good_nodes = set()
    
    for idx in path_indices:
        node = current_nodes[idx]
        if node['type'] == 'relay':
            if node['status'] == 'good':
                found_good += 1
                visited_good_nodes.add(node['name'])
            elif node['status'] == 'damaged':
                found_bad += 1
    
    msg = f"Result: Found {found_good}/{good_sats_total} Good Sats. Bad Sats: {found_bad}."
    if found_good >= 1:
        msg += " -> PASS (>=1 Good)"
    else:
        msg += " -> FAIL (Need >=1 Good)"
        
    return msg

# --- 主循环 ---
running = True
clock = pygame.time.Clock()

while running:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                current_nodes, good_sats_total = generate_hidden_level_data()
                path_indices = []
                message = "Regenerated. Good Sats Hidden."
            elif event.key == pygame.K_RETURN:
                message = check_result()
            elif event.key == pygame.K_r: # Reset path
                path_indices = []
                message = "Path Cleared"
            elif event.key == pygame.K_s: # Show cheat
                message = f"CHEAT: Good Sats Total = {good_sats_total}"
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                idx = get_node_at_pos(event.pos)
                if idx is not None:
                    if idx in path_indices:
                        path_indices.remove(idx)
                    else:
                        path_indices.append(idx)

    # Drawing
    screen.fill(BG_COLOR)
    
    # Draw connections
    if len(path_indices) > 1:
        points = [current_nodes[i]['pos'] for i in path_indices]
        pygame.draw.lines(screen, ACCENT_COLOR, False, points, 2)
    
    # Draw Nodes
    for i, node in enumerate(current_nodes):
        x, y = node['pos']
        
        # Color based on selection
        color = (100, 100, 100) # Default grey
        if i in path_indices:
            color = (255, 255, 255) # Selected
        
        # Type specific
        if node['type'] == 'src': color = (50, 200, 50)
        if node['type'] == 'dest': color = (200, 50, 50)
        
        # Debug Visualization (Hold TAB to see truth)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_TAB]:
            if node.get('status') == 'good': color = (255, 215, 0) # Gold
            if node.get('status') == 'damaged': color = (100, 0, 0) # Dark red
            
        pygame.draw.circle(screen, color, (int(x), int(y)), 15)
        
        # Draw Label
        lbl = font.render(node['name'], True, (200, 200, 200))
        screen.blit(lbl, (x+20, y-10))

    # UI Overlay
    pygame.draw.rect(screen, (30, 30, 40), (0, 0, WINDOW_WIDTH, 80))
    
    info_text = header_font.render("HIDDEN LEVEL DEBUGGER", True, ACCENT_COLOR)
    screen.blit(info_text, (20, 20))
    
    status_text = font.render(message, True, SUCCESS_COLOR)
    screen.blit(status_text, (20, 55))
    
    instr = [
        "[Left Click] Toggle Node",
        "[SPACE] Regenerate Level",
        "[R] Clear Path",
        "[ENTER] Check Result",
        "[TAB] Hold to Reveal Good Sats"
    ]
    for k, line in enumerate(instr):
        t = font.render(line, True, (150, 150, 150))
        screen.blit(t, (WINDOW_WIDTH - 250, 20 + k*25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
