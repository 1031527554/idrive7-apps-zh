# 本 fork 对 ambient_config 的改动（idrive7-apps-zh）

上游 `apps/ambient_config` 是氛围灯控制应用。本 fork 在它上面加了**三种"自动"动画**（车主 2026-11-11 需求）：

| 动画 | 做什么 | 由谁决定 |
|---|---|---|
| **Colour cycle**（循环变色） | 整车内饰灯在**调色板**范围内持续循环变色，环形过渡 | `scene.palette`：Every colour / Cool / Warm / M colours；周期随 Speed 档变化 |
| **Beat**（节拍） | 按设定的**每分钟节拍**脉动：瞬间到顶，然后递减到下一拍 | `scene.bpm`：60–180（7 档） |
| **Follow driving**（随驾驶变化） | 随车实时变化：怠速蓝 → 高转红，亮度随油门状态 | `scene.source`：Revs / Speed / G-force |

## 为什么这样实现（而不是"逐拍闪灯"）

经网关**一次只能一个 UDS 写、约 200 ms**，一次静止颜色保持 60 s、动画保持 5 s。逐拍闪灯需要远高于此的刷新率，做不到；所以"节拍"做成**亮度包络**（瞬间到顶→递减），"随驾驶"做成**颜色/亮度的平滑跟随**。同一时刻整条总线用 NAD 0 广播，所以一个颜色 **2 次写/帧**（两条总线），这是 `lights.js` 已有的优化，未改动。

## 改了哪些文件

| 文件 | 改动 |
|---|---|
| `apps/ambient_config/scenes.js` | `KINDS`/`NAMES` 增加三种；`lightAt` 增加三个 `case`；新增 `PALETTES`/`PALETTE_NAMES`/`CYCLE_MS`/`DEFAULT_BPM`/`BEAT_FLOOR` 常量并导出 |
| `apps/ambient_config/control.js` | 新增 `car`（实时车辆值）持有；`_show()` 把实时值**附加**到场景上（不持久化、不参与"已显示"去重，避免每帧重置动画） |
| `apps/ambient_config/main.js` | `require('./kit/car')`；`background()` 里 `new Car(bg, ['rpm','speed','accel'])` 并 `onSample` 更新实时值；Animations 页重排为 2 列 8 项 + 每种动画各自的参数行；预览带上实时值；`control` 接收 `car` |
| `apps/ambient_config/app.json` | 信号权限新增 `vehicle.CDS.statusEngineSpeed2`、`vehicle.Vehicle2.statusCarSpeed2`、`vehicle.CDS2.statusLongitudinalAccelerationMassCenter`/`statusLateralAccelerationMassCenter`（**全部照抄 gforce/redline 的既有声明与 `rs` 标志**）；新增可见设置 `demo`（Demo data: Auto/Always/Never，与其它 13 个应用一致） |
| `kit/tools/test_ambient_auto.js` | **新增**测试（不随构建上车的测试文件） |
| `fork-tools/zh-CN-supplement.json` | 新增 14 条中英对照（本 fork 新增文案的简体中文） |

**未改**：`lights.js`（时序/写调度保护原样保留）、`lin.js`、`ambient.js`、`cabin.js`。

## 车辆数据从哪来

`kit/runtime/car.js` 负责：BMW 官方标定（转速 ×0.25、车速 ×0.015625、加速度 ×0.002−65）、把加速度换算成 g、以及**没有车应答时自动切到内置 demo 模拟**（所以台上也能看到动画在动）。因此本功能**不需要**任何新权限之外的东西，也不需要音频数据源。

## 测试

```sh
node kit/tools/test_ambient_auto.js      # 本 fork 新增：三种动画（27 项）
node kit/tools/test_ambient_config.js    # 上游：模式/色槽/节流（21 项）
node kit/tools/test_ambient_rgb.js       # 上游：LIN/写帧/场景（53 项，其中 rainbow 一项为上游自带竞态，在上游原版上同样失败）
```

模拟器：`kit/emu`（`docs/emulator.md`）。真车：把本 fork 作为 Store 源构建安装后，Animations 页选三种之一即可；`Follow driving` 在台上会自动用 demo 数据演示。

## 与上游同步的关系（重要）

`apps/ambient_config/` 已列入 **`fork-tools/keep.json`**，因此 `fork-tools/sync_upstream.py`：
- **不再覆盖**本目录（复制与三方删除都跳过）
- 但会**报告上游对本目录的改动**（新增/修改/删除），需要人工合并

所以上游若更新了这个应用，请按 `sync_upstream.py` 的输出手工合并，重点是 `scenes.js`（新增动画）与 `main.js`（Animations 页布局）。

## 首次进入要自己先画一帧（2026-11-20）

车主反馈：**第一次**打开这个应用时画面像"卡住"、缩放/比例不对、点哪里都没反应；**退出再进就正常**。

原因在启动顺序，不是应用坏了：

- `start(ctx)` 第一件事是 `await background(ctx)`，而 `background()` 要**开诊断会话**（`Diag.init()`）并**搜灯**
  （`Ambient.start()` / `lights.find()`）——车机上每个 UDS 请求约 200 ms，累计是"几秒"量级；
- 在应用画出第一帧之前，HMI 的框里还是它自己的**页面滑入/放大动画状态**
  （`display.js` 注释原文：*the HMI zooms / slides its page in … the picture shows once the page stands
  where it ends, not shifted and too big for a moment*）→ 看起来就是"比例不对 + 不动"；
- 而 `ctx.onTab` / `ctx.onTap` 是在 `await` **之后**才注册的 → 这段时间点击无人接收；
- 退出再进时 kit 已缓存 `ctx.background` → 立刻出帧 → 一切正常（所以"只有第一次"）。

修法（`main.js`）：`start()` 一进来**先画一帧并交给 HMI**（标题 + `Starting...`），并**先注册一个临时
`ctx.onTab`** 记住被按下的标签页；后台就绪后再注册真正的处理器（kit 的 `onTab` 是覆盖语义），并把记住的
那一页应用上去。于是首屏立刻有内容、比例正确、启动期间的点击也不会丢。

测试：`kit/tools/test_ambient_pages.js` 现在断言"**后台之前已经呈现过一帧**"（撤掉这段修复该断言即失败）。
