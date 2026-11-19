# idrive7-apps-zh — 中文构建 fork（供 MGU Store 自建源使用）

本 fork 的目的：**让 `idrive7-apps` 那批应用以中文界面、并且通过 Store 自建源安装和管理。**

上游：`cauliflowermossgrape/idrive7-apps`（本 fork 基于其 `main` 于 2026-11-07 的快照）。
上游原样保留：`LICENSE`、`NOTICE.zh-CN.md`、`README*.md`、`kit/`、`apps/`、`deploy/`、`docs/`、
以及**中文 UI 语料** `kit/runtime/locales/zh-CN.json`（译名来自该目录，未改动）。

**状态：已发布，并已在真车验证通过。**

- 已发布：**https://github.com/1031527554/idrive7-apps-zh**（公开，分支 `main`）
- 真车结果（车主 2026-11-09 确认）：**当时 14 个应用全部经 Store 从本源自建并安装成功，界面均为中文**
- 上游同步：2026-11-09 加入 `ambient_config`；**2026-11-11 再次同步，15 个应用全部升级**
  （`redline 2.0.20` 含整套 HUD、`ambient_config 2.0.4`、`dyno 1.6.1` 等）。
  **2026-11-11 这批升级尚未上车验证**
- **2026-11-12 同步**（上游 7 新增 / 28 修改 / 0 删除）：上游给 `ambient_config` 加了 `others.js`
  ——检测 IterioDev 的 Comfort 工具也在写同一批氛围灯，并在界面提示卸载它（`app.json` 只动了版本号）。
  该目录受保护，故**人工合并**进本 fork 的版本：保留我们的三种自动动画与中文改动，加入 `others.js`、
  `Others` 接线、`warnOthers()` 警告（**先翻译再折行**，否则折行后的字符串无法匹配词典），
  并把版本提到 **2.0.6**（上游这次也是 2.0.5，我们必须更高才收得到更新）。
  同时同步了 `redline` 的 `logview.js`/`shareshift.js`、`kit/runtime/*`、`mgu-repo.json`（renderer 工具去掉
  `provides` 字段）等；补充表补了 2 条新文案（"Another ambient app" 与那段警告），图集重烘为
  **966 字形**（+8，仍 44 号字、1024×1839）。**这批同样尚未上车验证。**
- **2026-11-16 同步**（上游 21 新增 / 116 修改 / 0 删除）：上游给 `ambient_config` 加了**远光爆闪（strobe）**
  与灯光秀、转向灯流光、开门红灯、双闪红灯等，版本 **2.0.5 → 2.5.0**（`strobe.js` 721 行 + main.js +246 行）；
  `redline` 2.0.38 → 2.0.42，共 9 个应用涨版本。上游同时把**依赖声明从 `mgu-repo.json` 挪进了各
  `apps/<id>/app.json`**（`requires`），并新增 `kit/renderd/inputgate/tool`（inputgate 成为独立可装工具）。
  本 fork 的处理：
  - 受保护目录**人工三方合并**（base=11-12、ours=fork、theirs=11-16）：`scenes.js`/`lights.js` 零冲突直取；
    `app.json` 的版本冲突取上游 2.5.0；`control.js` 2 处、`main.js` 5 处逐处合并（保留我们的三种动画、
    `live` 车辆值、中文改动；采纳上游的 strobe 接线与"先翻译再折行"，但**保留我们按字符折行的 `wrapText`**，
    因为中文没有空格）。上游 2.5.0 自己也在 `warnOthers()` 里做了"先翻译"，与我们的思路一致。
  - **修了一个同步新引入的回归（BLOCKER，由队友独立发现）**：`gen_mgu_repo.py` 原来给每个 component 写
    `"requires": {}`，而 Store 的取值是 `entry[k] !== undefined ? entry[k] : app[k]`（`sources.js` 的 `pick()`）
    ⇒ 空对象**遮蔽**了 app.json 里的依赖，从本源自建将**不再自动带上 `idrive7-renderd` 与 `mgu-inputgate`**
    （失去 iDrive 控制器/GPU 渲染器）。现改为**合并上游块与各 app.json 的 `requires`，为空时不写该键**；
    `mguHmi` 同理（不再钉成 `["ID7"]`，恢复 `["ID7","ID8"]`）。队友用 Store 自己的 `repoCatalog` 复现：
    修复前 `NO`、修复后 `YES`（与上游 11-16 树逐条相同）。
  - 补充表 210 → **304 键**（Strobe 页与新增设置项全部中文），图集重烘 **980 字形、1024×1882、仍 44 号字**。
    **这批尚未上车验证。**
- **2026-11-18 同步**（上游 20 新增 / 2 删除 / 78 修改）：**15 个应用全部涨版本**，`ambient_config 2.5.0 → 2.7.6`
  （新增**拨杆启动爆闪** `lever.js`、`lightsKnown` 记忆上次找到的灯、以及**更硬的 Comfort 冲突提示**：
  改为一句话说明"本应用已停止改灯"并**用红色显示**）；新增 `kit/runtime/{qr,qrlog,twin_dme}.js`
  （二维码日志）与 `apps/{draggy/wheelspin,edrive/linkqueue,warmup/coldstarts}.js`、
  `apps/redline/{electrical,fuel,knock}.js` 等。本 fork 的处理：
  - **app.json 这次改为语义合并**：上游 2.7.6 为基（含新设置 `strobeLever`/`strobeLeverDriving`/`doorCar`
    与新信号 `statusLightStatus`/`vehicleConditionNoCrc`），补回本 fork 的 `CDS`/`CDS2` 信号
    （随驾驶变化用）与上游已删但 `kit/car.js` 仍在读的 `demo` 设置。
    **原因**：文本三方合并会在 `Vehicle2` 处产生**重复键**（两侧位置不同）——改用 JSON 合并避免。
  - `main.js` 三处冲突：保留我们的 CJK 感知 `wrapText`、`live` 车辆值与"先翻译再折行"，
    采纳上游的新提示文案、宽度自适应的标题与红色配色、以及 `lights.js` 的 `known` 参数；
    `control.js`/`lights.js`/`lin.js`/`scenes.js`/`others.js` **零冲突**直取；`lever.js` 为新文件。
  - **再次复用"真渲染"验证**（见下条纪律）：`build.py --preview-only` + `test_ambient_pages.js` **13/0**，
    确认这次没有再丢声明。
  - 汉化：补充表 304 → **316 键**（新提示两种长度、拨杆三个设置项、拨杆开关状态），
    **删掉被上游改写的旧警告键**（避免死键）；图集重烘 **977 字形、1024×1882、仍 44 号字**；
    i18n 仿真 **184 条 0 英文**。**这批尚未上车验证。**
  - **非 ambient 应用的汉化（同日追加，提交 `e2a2142`）**：14 个应用 + `kit/runtime/*` 的界面文案
    （本轮新模块 119 条 + 历史遗留 45 条，共 **164 条**）并入补充表 → **480 键**；
    **480 条全部过真 `i18n.js` 校验：0 条保持英文、0 条无中文**（26 条按预期保留品牌/单位拉丁字母）。
    顺带修掉两处"**字典自己把句子改坏**"的缺陷（`full-throttle` 被短词拆成"满电-节气门"、
    `Redline's HUD is off in …` 被改成"换挡转速's HUD is off 舒适"）——用整串键解决。
    字典解决不了的两处已记录并建议上游改代码：`qrlog.js` 的 `Page 1 of 3`（`of` 两侧是数字，无词组边界）、
    `live_data` 的 `min`（分钟/最小值同形）。
    图集重烘 **997 字形、1024×1925、仍 44 号字**（余量约 120 px ≈ 60 个字，**下一批字形要留意预算**）。
    为让车机真正重建、拿到译文与新图集，**11 个涉及应用涨补丁版本**：redline 2.0.46、live_adjustments 0.9.9、
    service 1.6.4、zf8hp 1.5.9、live_data 1.0.18、edrive 2.11.1、dtc_scanner 2.9.9、warmup 1.9.1、
    car_vitals 2.27.9、dyno 1.6.4、draggy 2.6.1（`brake_test`/`doom`/`gforce` 未涨：它们自身文案已由上游目录覆盖，
    只有 kit 级"QR log"设置页那一行仍是英文）。

## 与上游的差异（只有这些）

| # | 文件 | 改动 | 原因 |
|---|---|---|---|
| 1 | `mgu-repo.json` | 用 `components: [...]` **逐条列出 15 个应用**（上游是 `apps: {"path": "apps/*"}` 单条 pattern），每条带 `title`/`description`/`texts['zh-CN']`；`build.args` 改为 `["{id}", "--language", "zh-CN"]` | ① 让车机侧构建中文；② 让 Store 列表显示中文名（`sources.js` 的 `pick()` 优先取本条目的值，`catalog.js` 的 `textsOf()` 接受 `zh-CN`）。pattern 形式无法逐 app 给不同文案 |
| 2 | `kit/tools/localize.py` | 两处：`package_version()` **只对 `zh-CN`** 返回原版本（不再追加 `-zh.cn.<rev>`）；`load_locale()` 为 `zh-CN` **合并 fork 补充表**（上游条目优先） | 前者：Store 目录校验只接受 `x.y.z`（`catalog.js` 的 `SEMVER`），deploy 工具也按 `preinstalled_apps/<id>@<x.y.z>.tgz` 命名（`mgu-deploy.js:5382`），带后缀的包**既不能发布也不能安装**。后者：上游语料没跟上的界面文案先用补充表填上 |
| 3 | `fork-tools/`（新增） | `gen_mgu_repo.py`（重建清单）、`sync_upstream.py`（一键同步）、`keep.json`（**保护路径**）、`test_sync_keep.py`（保护机制的验收脚本）、`zh-CN-descriptions.json`（Store 列表描述）、`zh-CN-supplement.json`（上游语料未覆盖的界面中文） | 上游升级后一条命令重建；补充表不改上游语料、同步自动保留 |
| 4 | `mgu-repo.json.upstream`（新增） | 上游原始清单，供生成脚本读取 | 便于对照与回滚 |
| 5 | `apps/ambient_config/`（**受保护**） | 新增三种自动动画：**循环变色 / 节拍 / 随驾驶变化**（转速、车速、G 值），Animations 页重排为 8 项并各自的参数行；`app.json` 增加车辆信号权限与 `demo` 设置。详见 `apps/ambient_config/FORK.md` | 车主需求；该目录列入 `fork-tools/keep.json`，**同步不会覆盖**（只会上报上游改动供人工合并） |
| 6 | `kit/tools/test_ambient_auto.js`（新增） | 上述三种动画的测试（27 项） | 测试文件不随构建上车 |
| 7 | `kit/runtime/fonts/cjk.json`（**受保护**） | 本 fork **自己烘焙**的中文字形图集（958 字形、1024×1839 px、44 号字）：把上游语料 + 本 fork 补充表的字一起烘进去 | 上游的 `bake_cjk.py` 只烘 `zh-CN.json` 里的字，本 fork 的译文缺字会画成 `?`。见下节"中文是怎么显示的" |
| 8 | `fork-tools/bake_cjk_fork.py`、`check_glyphs.py`、`README-bake.md`（新增） | fork 版烘焙流水线与缺字检查 | 上游改语料或我方改补充表后，一条命令重新烘焙 |

`build`/`requires`/`mguHmi`/`tools` 的值**全部照抄上游**（`python: kit/tools/build.py`、`sdk: oap-sdk`、
`output: dist/{id}@{version}.tgz`、`requires: {idrive7-renderd: 2.1.7, mgu-inputgate: 1.0.0}`），未自行发明。

## 为什么必须这样改（三条硬约束）

1. **构建语言没有运行时开关。** 上游 README 明确：包是 fixed-language，没有 Settings→Language；
   `build.py` 的 `--language` 默认 `en`。所以只能改"让车机带着 `--language zh-CN` 去构建"。
2. **产物名/版本必须是纯 `x.y.z`。** `--language zh-CN` 原本会让版本变成 `x.y.z-zh.cn.5`，
   而 Store 目录校验（`SEMVER`）与 deploy 工具的包名正则都不接受后缀 → 故让 `package_version()`
   **只对 `zh-CN`** 保持原版本（`ru`/`ko` 仍走上游逻辑，避免影响本 fork 不使用的路径）。
3. **列表文案来自目录 `texts`。** Store 的 `i18n.text()` 取 `texts['zh-CN']`，取不到才回退英文 `title`；
   而目录条目优先取 `mgu-repo.json` 的值 → 故逐条写 `texts`。

## 发布与安装（车主操作）

1. **推到自己的 GitHub 仓库 —— （已完成）** 本 fork 已发布为
   **https://github.com/1031527554/idrive7-apps-zh**（公开，分支 `main`）。
   如需在别处重建，命令：
   ```powershell
   cd D:\id7\idrive7-apps-zh
   git remote add origin https://github.com/<用户名>/idrive7-apps-zh.git
   git push -u origin main
   ```
   > 仓库内**不含** BMW SDK：`oap-sdk/` 由车机的 mgu-deploy 生成后写入构建副本（`.gitignore` 已排除）。
2. **车机上加源**：Store → 设置 → **Add source** → 输入 `<你的用户名>/idrive7-apps-zh`
   → 在随后弹出的列表里选分支 **main**。
3. **先卸载英文版**（同一个 app id 且版本号相同，Store 不会把它当成更新）：
   在 Store 里逐个 Remove 你要替换的应用。
   ⚠️ 卸载可能清掉该应用的数据（行程记录、设置等）。刚装的可直接重来；有数据先记下来。
4. **安装中文版**：在 Store 里从新源安装。车机会**现构建**（Python + Node + 图标渲染），
   逐个应用需要一点时间；`doom` 构建时需要联网（`build.network: ["doom"]`），没 uplink 就跳过它。
5. 装好后可在 Store 里正常更新/卸载；列表名与应用内界面都应为中文。

## 限制与已知问题

- **翻译覆盖**：2026-11-11 为 **673/757（88%）**（同日加补充表前是 73%，11-09 为 80%，11-07 为 90%）。
  上游自 2026-11-09 起**没有更新** `kit/runtime/locales/zh-CN.json`，而 `redline` 从 128 条涨到 188 条；
  `redline` 现在 **166/188**，剩下 22 条是单位符号、字体名与纯温度值（`km/h`、`Nm`、`bar`、`Ubuntu`、
  `60 °C (140 °F)` 等）——**这些在任何语言里都应保持原样**，故有意不译。
  `ambient_config` 现在是 **18/18 满载**：它的设置页原本有 8 条英文（`Dimmer at night`、
  `My colour back at each start`、`Left`/`Right` 等）上游语料里没有，已由本 fork 的补充表补上。
  `service`、`warmup`、`dtc_scanner` 满载；`car_vitals`、`dyno`、`edrive`、`live_data`、`live_adjustments`
  剩余的也基本是单位与缩写，不算遗漏。
  上游译者补齐语料后重新同步即可：**上游条目始终优先**，被上游覆盖的补充表键会让位。
- 翻译由上游署名译者提供，**机器辅助、未逐句人工审校**（见 `docs/diagnostic-chinese.md`）；
  故障库说明可能存在术语错误。
- 本 fork **新增**的只有 `fork-tools/zh-CN-descriptions.json` 里的 14 条"列表描述"（Store 列表用），
  它们**不是**上游署名译者作品，已在文件内注明。
- 版本号与上游保持一致 ⇒ 无法以"更新"覆盖英文版，必须"先卸载再装"（第 3 步）。
- 与上游版本会分叉：上游升级后需 `git pull` 并重跑生成脚本。
- `.github/workflows/` 保留上游 CI（含需要 Docker 的 renderd 构建）；在 fork 上失败属正常，不影响本用途。

## 中文是怎么显示的（两个独立的坑）

车机上"英文残留"和"`?` 乱码"是**两个不同**的问题，本 fork 两边都要自己解决：

| 症状 | 原因 | 本 fork 的做法 |
|---|---|---|
| 还是英文 | 该字符串不在 `kit/runtime/locales/zh-CN.json` 里，而 kit 的运行时翻译只查这份词典 | 译文进 `fork-tools/zh-CN-supplement.json`，构建时由 `localize.load_locale()` 合并（**上游条目优先**） |
| `?` 方框 | canvas 文字用预烘**字形图集** `kit/runtime/fonts/cjk.json` 绘制，缺字回退成 `?`（`kit/runtime/fonts.js:47` → `glyphs[63]`）。上游烘焙脚本 `kit/tools/bake_cjk.py` **只烘 `zh-CN.json` 里的字**，本 fork 补充表的字没有字形 | 用 `fork-tools/bake_cjk_fork.py` 把**上游语料 + 补充表**一起烘焙；产物 `cjk.json` 已列入 `keep.json` |

**维护规则（重要）**：只要**改了补充表**，或**同步后上游改了 `zh-CN.json`**，就必须重新烘焙：

```powershell
python fork-tools/bake_cjk_fork.py                                    # 烘到 fork-tools/out/cjk.json
copy fork-tools\out\cjk.json kit\runtime\fonts\cjk.json
python fork-tools/check_glyphs.py --atlas kit/runtime/fonts/cjk.json  # 必须 0 缺字
```

预算：图集高度上限 **2048 px**，超出会自动降字号（48→44→40→36→32），那会让**所有应用**的中文一起变小。当前 1839 px（44 号字），余量约 200 px ≈ 100 个字形。

补充两点：
- 运行时翻译器对**短语替换只处理 ≥4 字符的键**（`kit/runtime/i18n.js:35`），所以 `Red` 这类短词只有在"整串精确命中"时才翻译。应用里拼接出来的句子（如 `Upper: Red, 80%`）因此改为用 `require('./kit/i18n').t()` **逐片段翻译**并让 `cv.text` 走 `literal`。
- 图集是**打进每个应用包**的（构建时复制 `kit/runtime`），所以修好图集后，车机上已装的每个应用都要**重新构建/更新**才会生效。

**几个必须知道的细节（2026-11-12 实测得出）**

- **图集是整块重渲染，不是"旧图集 + 加字"**：fork 版烘焙（Pillow 11.3.0 + 固定字体）与上游提交的图集
  存在 <0.4 px 级度量漂移（旧图集来自另一套 FreeType/字体构建）。真车上建议目视确认一次文本宽度与居中
  没有肉眼可见变化。另：**若上游自己重烘，他们会落在 48 号字**（更大）；我们用 44 号，字号不同属预期。
- **字体 SHA-256 常量有两份**：上游 `kit/tools/bake_cjk.py:20` 与 `fork-tools/bake_cjk_fork.py`。
  Google 重发 NotoSansSC 时两处都要更新，否则两边烘出的图集不一致（校验失败会硬停，安全但会阻塞）。
- **Pillow 版本会影响是否降级**：1839 px 距上限 2048 只剩 209 px（≈80–100 个字形）。换机器 / 换 Pillow
  可能直接掉到 40 号（**所有应用**的中文一起变小）。**不要跨环境 diff 图集文件**，只比覆盖率；
  烘焙脚本会打印试过的每个字号与高度，以及 `DOWNGRADE:` 警告。
- **审计范围**：`check_glyphs.py` 只看 `zh-CN.json` + 补充表两处文本；直接写在 app JS 里的中文不在审计内
  （缺字照样画 `?`）。提交前请连同 i18n 离线仿真一起跑（`research/simulate_i18n.js`，用 kit 自己的翻译器
  跑真实绘制字符串）。
- **`dtc_scanner` 用另一张图集**：`kit/localization/fonts/diagnostic-zh-CN.json`（32 号、1620 字形，上游烘焙，
  本 fork 暂无对应版本）。目前补充表中出现在 `apps/dtc_scanner/**` 的 6 条对它 0 缺字；若以后新增由
  Fault Scanner 绘制的文案，需要同样做一份 fork 版。
- **同步后**：`sync_upstream.py` 在检测到上游改过 `zh-CN.json` 时会**打印重烘提示**（图集在 `keep.json` 里
  受保护，不会被覆盖，所以不会"悄悄过期"）。
- **两个 fork-tools 的坑（2026-11-16 踩到并已修）**：  - `sync_upstream.py` 判定"哪些函数是我们的补丁"时，必须**以旧基线（第 3 个参数 `<old>`）为参照**。
    曾用"与新上游不同的函数"来判定，于是上游自己改过的 `unicode_resources()` 被误认成我们的补丁而
    **中止同步**（错误信息 "does not look like ours"）。现在：与旧基线不同 **且** 含 `zh-CN` 才算我们的补丁；
    我们补丁的函数若上游也改了，会明确拒绝并提示人工合并（不会静默丢掉上游的改动）。
  - `gen_mgu_repo.py` **不要写空的 `requires`/`mguHmi`**：Store 的 `pick()` 只判断 `!== undefined`，
    空对象会遮蔽各 `app.json` 里的声明（后果见上文的 BLOCKER）。
- **合并冲突时的纪律（2026-11-16 的教训，务必遵守）**：三方合并的冲突块里，**一方的整段可能包含必须保留的
  声明**（当时是 `let picked = '';`）。手动消解时只取数组/片段、丢掉那行声明，`node --check` 与所有逻辑测试
  **都发现不了**——要等真正渲染那一页才炸，车上的表现是"**画面正常但整个页面点不动**"
  （渲染循环抛异常 → 应用停止响应）。所以**凡改过 `apps/ambient_config/` 的绘制代码，必须跑**：

  ```powershell
  python kit/tools/build.py --language zh-CN --preview-only ambient_config
  node kit/tools/test_ambient_pages.js         # 逐页真渲染 + 模拟标签/点击，13 项
  ```

  `--preview-only` **不需要 SDK donor**，电脑上随时可跑；`test_ambient_pages.js` 会用 `kit/tools/hu-stub.js`
  把构建产物真正跑起来逐页绘制，专门抓这类"只在渲染时才报的作用域/API 错误"。

## 版本号约定

`apps/ambient_config/app.json` 的版本在本 fork 里会在**补丁位自增**（上游 2.0.4 → 本 fork 2.0.5），这样车机能经 Store 正常收到更新（同版本 Store 不会重建）。同步上游时若上游版本更高，以上游为准，然后我们再自增。

> **铁律（2026-11-19 踩坑后写死）：本 fork 的版本必须始终 ≥ 上游 + 1 个补丁位，任何时候都不能与上游持平。**
> 原因：车机的 Store 里通常同时挂着上游源与本 fork 源，同一个 app id 在两处都有；而**上游清单的 `build.args` 只有 `["{id}"]`（没有 `--language`）**，
> `kit/tools/build.py` 的默认语言是 `en` ⇒ **从上游源构建出来的是英文包**。一旦我们的版本落后或与上游持平，
> Store 就会把上游那份当成"更新"推给你，装上去就是**整页英文**（2026-11-19 车主遇到的就是这个：上游发到 2.7.6 时我们还在 2.5.1）。
> 判别方法：打开应用看标签页——`颜色/动画/驾驶模式/收藏` 是我们的中文构建，`Colour/Animations/…` 是上游的英文构建。
> 加固：**把上游的 `idrive7-apps` 源从 Store 里删掉/停用**，只留本 fork 源，从根上消除歧义。



上游一有更新就跑这三步（`fork-tools/sync_upstream.py` 会做"覆盖为上游树 → **删除上游已移除的文件** →
保留本 fork 的文件 → **重贴 `localize.py` 里所有被改动过的顶层函数**（目前是 `load_locale()` 与
`package_version()`）→ 刷新 `mgu-repo.json.upstream` → 重新生成 `mgu-repo.json`"）：

> **保护路径**：`fork-tools/keep.json` 里列的路径（目前是 `apps/ambient_config/`）**永不被覆盖也不被删除**，
> 上游对这些路径的改动只会被**列出来**（新增/修改/删除）供人工合并。`keep.json` 缺失时脚本会拒绝同步，
> 不会静默回到旧语义。破坏性验证可在 fork 副本上跑 `python fork-tools/test_sync_keep.py`。

```powershell
# 1) 取上游当前 main 并解压
curl.exe -sSL -o up.tgz https://codeload.github.com/cauliflowermossgrape/idrive7-apps/tar.gz/refs/heads/main
tar -xzf up.tgz -C _upstream

# 2) 一条命令同步（第 3 个参数给旧基线时，还会列出应用版本与描述的变化）
python fork-tools\sync_upstream.py _upstream\idrive7-apps-main .

# 3) 校验并推送
node ..\validate_fork_source.cjs        # 用 Store 自己的解析器验清单
python ..\dryrun_localize.py .          # 覆盖率 + 未译条目
git add -A; git commit -m "sync upstream main"; git push
```

同步后请检查两处（脚本会提示）：

- **`descriptions changed upstream`**：上游改了某应用的英文描述 → 人工更新
  `fork-tools/zh-CN-descriptions.json` 里对应的中文描述，再重跑 `gen_mgu_repo.py`。
- **上游新增应用** → `gen_mgu_repo.py` 会打印 `no fork description for: <id>`，补一条中文描述即可
  （标题会自动取上游中文语料）。

安全阀：若上游改动了 `kit/tools/localize.py` 的 `package_version()`，脚本会**拒绝盲同步**
（`refuse to sync blindly`），需要人工合并后再跑。

## 验证记录（2026-11-07，全部为电脑侧离线验证）

- **用 Store 自己的解析器**（mgu-updater `sources.js` 的 `repoCatalog`）解析本 fork：
  `components=16`（14 app + 2 tool）、`skipped=0`、每个 app 的 `script.args = ["<id>","--language","zh-CN"]`、
  `output = dist/<id>@<version>.tgz`、版本为纯 `x.y.z` 且与各自 `app.json` 逐条一致、`mguHmi=["ID7"]`、
  `requires` 含自动派生的 `mgu-python 1.0.2` 与 `mgu-deploy 0.3.2`、`texts['zh-CN']` 中文标题+描述 14/14。
- **与上游的差分测试**（同一 `package_version()` 双份导入对比）：

  | language | 上游 | 本 fork |
  |---|---|---|
  | `en` | `1.12.2` | `1.12.2` |
  | `zh-CN` | `1.12.2-zh.cn.5` | **`1.12.2`** |
  | `ru` | `1.12.2-ru.1` | `1.12.2-ru.1` |
  | `ko` | `1.12.2-ko.1` | `1.12.2-ko.1` |

  ⇒ **只有 `zh-CN` 与上游不同**，`en`/`ru`/`ko` 逐字一致（早期版本曾把该函数整体替换，
  连 `ru`/`ko` 的后缀一并去掉，已收窄为只处理 `zh-CN`）。
- **本地化 dry-run**：15 个应用逐条本地化，界面字符串 **757 条译出 673 条（88%）**（明细见上文"限制"）。
- **应用自带测试**（`node kit/tools/test_*.js`）：`test_ambient_auto.js`（本 fork 新增，27 项）与
  `test_ambient_config.js`（21 项）全部通过；`test_ambient_rgb.js` 53 项中有 1 项
  （`rainbow: the whole car one colour, 2 writes a frame`）为**上游自带的竞态断言**——
  在上游原版快照上同样稳定失败（各 3/3 次），与本 fork 的改动无关。
- **整树差异**（与上游快照逐文件比对）= **新增 10 + 修改 6 + 删除 0**：
  新增 `FORK-NOTES.md`、`apps/ambient_config/FORK.md`、`fork-tools/{gen_mgu_repo,sync_upstream,keep,test_sync_keep}`、
  `fork-tools/zh-CN-{descriptions,supplement}.json`、`kit/tools/test_ambient_auto.js`、`mgu-repo.json.upstream`；
  修改 `apps/ambient_config/{app.json,control.js,main.js,scenes.js}`、`kit/tools/localize.py`、`mgu-repo.json`。
  `kit/tools/build.py`、`apps/ambient_config/lights.js`、`kit/runtime/**`、`LICENSE`、`NOTICE.zh-CN.md`、
  `kit/runtime/locales/zh-CN.json` 等与上游**逐字节相同**。
- **中文显示（2026-11-12 加）**：
  - **i18n 离线仿真**（`research/simulate_i18n.js`，用 kit 自己的 `i18n.js` + 构建时同样的词典合并规则）：
    ambient_config 的 **94 条真实绘制字符串（含运行时拼接的句子）0 条残留英文**。
  - **字形覆盖**：`fork-tools/check_glyphs.py` 报 **0 缺字**（上游语料 + 本 fork 补充表）；
    图集 **958 字形、1024×1839 px、44 号字**（预算 2048，未降级）。
  - 修复前：补充表 128 条中有 37 条缺字形、`Colour`/`Speed` 等键与其它应用语义冲突（已改为"颜色"、
    并把动画速度的代码字符串改为 `Animation speed`），车机上表现为 `?` 与英文残留。
- **保护路径机制**（`fork-tools/keep.json`）：由另一位队友实现并独立验收（20/20 通过）：在 fork
  **副本**上模拟"上游改/删/增保护目录里的文件"→ 保护内容零改动、上游改动被逐条列出；真 fork 上跑
  幂等同步，前后全树 680 个文件逐字节不变；缺 `keep.json` 时脚本拒绝同步（不静默降级）。
- **独立只读复核**（另一个 agent，未参与本 fork 编写）：结论 **无 BLOCKER，可安全公开推送** ——
  已跟踪的 611 个文件里无 VIN、无私钥、无 `oap-sdk/`、无 `dist/`、无 token、无本机用户名/绝对路径；
  并独立复算了上述解析与整树差异。
- **真车验证（车主 2026-11-09 确认）**：14 个应用全部经 Store 从本源自建并安装成功，界面均为中文。
  该结论为**车主报告**，未由本仓库作者独立复核，逐应用的构建日志与界面证据未留存。
