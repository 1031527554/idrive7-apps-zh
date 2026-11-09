# idrive7-apps-zh — 中文构建 fork（供 MGU Store 自建源使用）

本 fork 的目的：**让 `idrive7-apps` 那批应用以中文界面、并且通过 Store 自建源安装和管理。**

上游：`cauliflowermossgrape/idrive7-apps`（本 fork 基于其 `main` 于 2026-11-07 的快照）。
上游原样保留：`LICENSE`、`NOTICE.zh-CN.md`、`README*.md`、`kit/`、`apps/`、`deploy/`、`docs/`、
以及**中文 UI 语料** `kit/runtime/locales/zh-CN.json`（译名来自该目录，未改动）。

**状态：已发布，并已在真车验证通过。**

- 已发布：**https://github.com/1031527554/idrive7-apps-zh**（公开，分支 `main`）
- 真车结果（车主 2026-11-09 确认）：**当时 14 个应用全部经 Store 从本源自建并安装成功，界面均为中文**
- 2026-11-09 已同步上游：现在共 **15 个应用**（新增 `ambient_config 1.1.0`；另有 4 个升级：
  `edrive 2.8.3`、`live_adjustments 0.9.0`、`redline 1.15.2`、`service 1.6.0`）。新增的这个应用**尚未上车验证**

## 与上游的差异（只有这些）

| # | 文件 | 改动 | 原因 |
|---|---|---|---|
| 1 | `mgu-repo.json` | 用 `components: [...]` **逐条列出 14 个应用**（上游是 `apps: {"path": "apps/*"}` 单条 pattern），每条带 `title`/`description`/`texts['zh-CN']`；`build.args` 改为 `["{id}", "--language", "zh-CN"]` | ① 让车机侧构建中文；② 让 Store 列表显示中文名（`sources.js` 的 `pick()` 优先取本条目的值，`catalog.js` 的 `textsOf()` 接受 `zh-CN`）。pattern 形式无法逐 app 给不同文案 |
| 2 | `kit/tools/localize.py` | `package_version()` **只对 `zh-CN`** 直接返回版本号（不再追加 `-zh.cn.<rev>`）；`en` / `ru` / `ko` 的行为与上游**完全一致** | Store 的目录校验只接受 `x.y.z`（`catalog.js` 的 `SEMVER`），deploy 工具也按 `preinstalled_apps/<id>@<x.y.z>.tgz` 命名（`mgu-deploy.js:5382`）。带上后缀的包**既不能发布也不能安装** |
| 3 | `fork-tools/`（新增） | `gen_mgu_repo.py`（重新生成 `mgu-repo.json`）、`zh-CN-descriptions.json`（列表描述中文） | 上游升级后可用一条命令重建清单；见下方"重新生成" |
| 4 | `mgu-repo.json.upstream`（新增） | 上游原始清单，供生成脚本读取 | 便于对照与回滚 |

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

- **翻译覆盖率随上游功能增长而下降**：2026-11-09 同步后，691 条界面字符串译出 559 条（80%）。
  `ambient_config`、`service`、`warmup`、`dtc_scanner` 等为满载；`edrive`、`live_adjustments` 剩余的是单位
  （`0 %`、`2,500 rpm`）；但 **`redline` 只剩 56/128** —— 上游新加的 HUD/仪表设置
  （`80s digital dash`、`Boost unit`、`Burst (pops, ring)`…）中文语料尚未覆盖，这些条目在应用里会显示英文，
  等上游译者补齐后重新同步即可。上游有意保留的单位与缩写（`km/h`、`Nm`、货币代码等）不算遗漏。
- 翻译由上游署名译者提供，**机器辅助、未逐句人工审校**（见 `docs/diagnostic-chinese.md`）；
  故障库说明可能存在术语错误。
- 本 fork **新增**的只有 `fork-tools/zh-CN-descriptions.json` 里的 14 条"列表描述"（Store 列表用），
  它们**不是**上游署名译者作品，已在文件内注明。
- 版本号与上游保持一致 ⇒ 无法以"更新"覆盖英文版，必须"先卸载再装"（第 3 步）。
- 与上游版本会分叉：上游升级后需 `git pull` 并重跑生成脚本。
- `.github/workflows/` 保留上游 CI（含需要 Docker 的 renderd 构建）；在 fork 上失败属正常，不影响本用途。

## 同步上游更新

上游一有更新就跑这三步（`fork-tools/sync_upstream.py` 会做"覆盖为上游树 → 保留本 fork 的文件 →
重贴 `localize.py` 补丁 → 刷新 `mgu-repo.json.upstream` → 重新生成 `mgu-repo.json`"）：

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
- **本地化 dry-run**：14 个应用逐条本地化，界面字符串 577 条译出 522 条（90%）；未译项为
  `km/h`、`mph`、`Nm`、`PS`、`bar/psi`、货币代码等上游有意保留的单位与缩写。
- **整树差异**（与上游快照逐文件比对）= 新增 4（`FORK-NOTES.md`、`fork-tools/` 两个文件、
  `mgu-repo.json.upstream`）+ 修改 2（`mgu-repo.json`、`kit/tools/localize.py`）+ 删除 0；
  `kit/tools/build.py`、`LICENSE`、`NOTICE.zh-CN.md`、`apps/*`、`kit/runtime/locales/zh-CN.json`
  等与上游**逐字节相同**。
- **独立只读复核**（另一个 agent，未参与本 fork 编写）：结论 **无 BLOCKER，可安全公开推送** ——
  已跟踪的 611 个文件里无 VIN、无私钥、无 `oap-sdk/`、无 `dist/`、无 token、无本机用户名/绝对路径；
  并独立复算了上述解析与整树差异。
- **真车验证（车主 2026-11-09 确认）**：14 个应用全部经 Store 从本源自建并安装成功，界面均为中文。
  该结论为**车主报告**，未由本仓库作者独立复核，逐应用的构建日志与界面证据未留存。
