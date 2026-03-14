# Pip-Boy 风格 UI 改造实施步骤（Pygame 项目）

适用项目：`signal_flow_game`  
目标：将当前 UI 视觉升级为参考图中的「复古终端 / CRT / 荧光绿」风格，在不改变核心玩法逻辑的前提下完成可持续维护的界面改造。

---

## 0. 改造目标与边界

### 0.1 目标（必须达到）

- 全局视觉从「蓝灰科技风」切换到「深绿黑 + 荧光绿」。
- 主要界面（开始页、关卡简报、进行中 HUD、设置页）风格统一。
- 增加 CRT 观感：扫描线、轻微噪点、暗角、微闪烁（可配置）。
- 交互可读性不下降：关键信息（预算、BER、SNR、按钮态）可清晰识别。

### 0.2 边界（本次不做）

- 不改关卡机制、数值平衡、存档格式。
- 不重构状态机结构。
- 不拆分成多文件大重构（先在 `main.py` 内完成一次稳定落地）。

---

## 1. 使用 `ui-ux-pro-max` 的设计系统流程（必做）

> 说明：本节用于先产出设计系统，避免“边改边拍脑袋”导致风格漂移。

### 1.1 生成设计系统（REQUIRED）

在项目根目录执行：

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "retro terminal pip-boy game HUD dark green CRT" --design-system -p "Signal Flow PipBoy"
```

Windows 没有 `python3` 时使用：

```powershell
python skills/ui-ux-pro-max/scripts/search.py "retro terminal pip-boy game HUD dark green CRT" --design-system -p "Signal Flow PipBoy"
```

### 1.2 持久化设计系统（推荐）

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "retro terminal pip-boy game HUD dark green CRT" --design-system --persist -p "Signal Flow PipBoy"
```

输出应包含：

- `design-system/MASTER.md`
- （可选）`design-system/pages/*.md`

### 1.3 补充查询（建议）

```bash
# 动画与可访问性
python3 skills/ui-ux-pro-max/scripts/search.py "animation accessibility reduced-motion contrast" --domain ux

# 配色和字体补充
python3 skills/ui-ux-pro-max/scripts/search.py "retro green monochrome terminal palette" --domain color
python3 skills/ui-ux-pro-max/scripts/search.py "monospace game UI readable chinese" --domain typography
```

---

## 2. 分阶段改造计划（按顺序执行）

## 阶段 A：视觉基线（1 天）

目标：先让项目 70% 像参考图。

### A1. 统一全局色板

文件：`main.py` 顶部颜色常量区域。

将当前蓝色系常量替换为单色绿系（建议值）：

- `BG_COLOR = (6, 12, 6)`
- `PANEL_COLOR = (10, 22, 10)`
- `MAP_BG_COLOR = (8, 16, 8)`
- `ACCENT_COLOR = (95, 255, 128)`
- `SUCCESS_COLOR = (130, 255, 150)`
- `ERROR_COLOR = (255, 110, 110)`
- `TEXT_COLOR = (150, 255, 170)`

验收标准：

- 启动后整体不再出现主蓝色调。
- 文字与背景对比明显（避免糊成一片绿）。

### A2. 字体策略切换（等宽终端优先）

文件：`main.py` `get_font_name()`、`load_safe_font()`。

做法：

- 优先字体列表改为：
  - `Cascadia Mono`
  - `Consolas`
  - `Lucida Console`
  - `Microsoft YaHei`（中文兜底）
- 保留本地字体文件兜底逻辑（你当前已实现，不要删）。

验收标准：

- 英文数字具备“终端字符”观感。
- 中文依然可显示（不出现方块字）。

### A3. 控件形态统一（硬边 + 发光边）

文件：`main.py` 中 `Button.draw()`、`Slider.draw()`，以及主要 `pygame.draw.rect` 面板调用处。

做法：

- 圆角从 `5~12` 统一下调到 `0~3`（终端硬边感）。
- 默认边框改为暗绿，激活/悬停改为亮绿。
- 按钮 hover 改“边框更亮/更粗”，不要大幅变色跳变。

验收标准：

- 按钮风格一致，不再有明显“网页按钮感”。
- hover 反馈清晰但不晃眼。

---

## 阶段 B：核心 CRT 效果（1 天）

目标：做出“屏幕设备感”，不是只改颜色。

### B1. 添加 `draw_crt_overlay(surface)` 统一后处理

文件：`main.py`（工具函数区）。

函数包含四层：

1. 扫描线（每 2~4 像素一条低透明黑线）
2. 噪点（少量随机像素，低 alpha）
3. 暗角（中心亮、边缘暗）
4. 轻微绿色 tint（整屏薄绿膜）

### B2. 在主渲染末尾调用

文件：`main.py` 主循环中，`pygame.display.flip()` 前。

伪顺序：

1. 先绘制所有游戏元素
2. 再调用 `draw_crt_overlay(screen)`
3. 最后 `flip/update`

验收标准：

- 所有状态界面都吃到同一后处理风格。
- 帧率下降可接受（目标 >= 55 FPS，最低不低于 45 FPS）。

性能提示：

- 避免在每帧重建大 Surface。
- 扫描线层、暗角层可预生成缓存，仅在分辨率变化时重建。

---

## 阶段 C：结构化终端 UI 语言（1~2 天）

目标：从“像”升级到“统一设计语言”。

### C1. 顶部导航条（Pip-Boy 视觉锚点）

新增顶部轻量导航文案（静态即可）：

- `STAT  INV  DATA  MAP  RADIO`

建议位置：

- 顶栏左上或中上区域，与当前关卡标题分层显示。

验收标准：

- 第一眼可识别复古设备 UI 语义。

### C2. 文本辉光（只给关键字）

关键文字（标题、激活参数、选中项）采用双层文本：

- 底层：深绿偏粗/偏大，低 alpha
- 上层：亮绿正常字

注意：

- 普通正文不要全加辉光，避免阅读疲劳。

### C3. 图标/符号统一

- 星级、锁图标、状态点使用统一描边风格与同一色域。
- 避免出现暖色和蓝色“突兀点”。

---

## 阶段 D：状态页面逐页收口（2 天）

目标：把风格覆盖到所有关键状态，避免“有的页面新，有的页面旧”。

按优先级执行：

1. `draw_start_screen`
2. `draw_briefing_screen`
3. 主游戏态 HUD（右侧配置面板 + 顶栏）
4. `draw_settings_screen`
5. `draw_level_catalog`
6. `draw_satellite_deployment_screen`

每个页面检查三件事：

- 颜色是否已切绿系
- 边框圆角是否统一
- 文本层级是否清晰（标题/标签/正文）

---

## 3. 面向你当前代码的具体改点清单

以下是本仓库可直接定位的改动入口：

- 颜色常量：`main.py` 顶部 `# --- 颜色定义 ---`
- 字体策略：`get_font_name()`、`load_safe_font()`
- 按钮：`class Button.draw`
- 滑条：`class Slider.draw`
- 开始页：`draw_start_screen`
- 简报页：`draw_briefing_screen`
- 游戏主 HUD：主循环中 `# HUD Background` 附近绘制逻辑
- 卫星部署页：`draw_satellite_deployment_screen`
- 全局后处理：新增 `draw_crt_overlay` 并在主循环末尾调用

---

## 4. 详细实施步骤（可逐条打勾）

## 4.1 预备

- [ ] 新建分支：`feature/ui-pipboy-style`
- [ ] 截图当前版本（开始页、关卡中、设置页）作为对照
- [ ] 记录当前 FPS（用于对比）

## 4.2 第一轮（只改色 + 字体）

- [ ] 替换颜色常量
- [ ] 调整字体优先级
- [ ] 快速跑通全部状态，修正不可读文本
- [ ] 重新截图对照

## 4.3 第二轮（控件统一）

- [ ] 改 `Button.draw` 样式
- [ ] 改 `Slider.draw` 样式
- [ ] 把最显眼 panel 的圆角统一为 0~3
- [ ] 处理 hover/selected 的色阶一致性

## 4.4 第三轮（CRT 叠层）

- [ ] 实现 `draw_crt_overlay`
- [ ] 主循环接入调用
- [ ] 做缓存避免掉帧
- [ ] 增加参数开关：`ENABLE_CRT = True`（便于排查）

## 4.5 第四轮（页面收口）

- [ ] 开始页顶部导航视觉锚点
- [ ] 简报页信息卡风格统一
- [ ] 游戏中 HUD 标题与卡片统一
- [ ] 设置/目录/部署页收尾

## 4.6 第五轮（微动画）

- [ ] 扫描线轻微滚动（可选）
- [ ] 随机亮度闪烁（低频，别刺眼）
- [ ] 保证动画不影响操作反馈

---

## 5. 质量与可读性标准（必须检查）

### 5.1 可读性

- 正文对比度满足可读（深背景 + 亮文字）。
- 颜色不是唯一状态信号：选中态同时有边框或符号变化。

### 5.2 交互

- 按钮 hover 和点击态可区分。
- 键鼠操作不受视觉层影响（overlay 只画，不拦截事件）。

### 5.3 性能

- 改造前后 FPS 差异可接受。
- overlay 引入后无明显输入延迟。

### 5.4 一致性

- 同级面板边框、圆角、间距一致。
- 不同页面使用同一色板，不混入旧蓝色风格。

---

## 6. 回滚与风险控制

### 6.1 建议开关

在 `main.py` 顶部增加：

- `ENABLE_PIPBOY_THEME = True`
- `ENABLE_CRT = True`

通过开关快速回退视觉层，不影响玩法逻辑。

### 6.2 常见风险

- 绿色过亮导致眼疲劳：降低 `ACCENT_COLOR` 亮度，缩小辉光范围。
- CRT 暗角过重：降低暗角 alpha。
- 噪点过多：减少数量和透明度。
- 低端机器掉帧：启用缓存、降低特效采样率。

---

## 7. 验收截图清单（交付必备）

至少提供以下截图用于验收：

1. 开始页（含顶部导航样式）
2. 关卡简报页（含信息卡）
3. 游戏进行中（地图 + HUD 同屏）
4. 设置页（按钮与滑条）
5. 卫星部署页（左右分栏）

每张截图要求：

- 标注“改前/改后”
- 标注主要变化点（配色、边框、CRT、可读性）

---

## 8. 建议提交粒度（便于排错）

建议拆成 4 次提交：

1. `feat(ui): switch to green terminal palette and mono font preference`
2. `feat(ui): unify button and panel visual language`
3. `feat(vfx): add optional CRT overlay pipeline`
4. `refactor(ui): apply pipboy style across all main screens`

---

## 9. 最终完成定义（Done Definition）

满足以下全部条件才算完成：

- [ ] 主视觉已统一为 Pip-Boy/CRT 风格
- [ ] 所有关键页面风格一致
- [ ] 关键文本可读性良好
- [ ] 不影响核心玩法与存档
- [ ] 性能在可接受范围
- [ ] 有改前改后截图可对比

