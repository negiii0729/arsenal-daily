# arsenal-daily 现状（已复核）

> 复核对象：`main` @ `021951d251b482a027bef5d69393536841b0210c`（2026-10-18 00:11:44 UTC，即 08:11 UTC+8）。
> 复核日期：2026-10-18。依据：仓库文件、`git log`、GitHub Actions 日志、Pages API、线上页面。
> 原稿是技术负责人的盘点。本文保留其结构，并改正与仓库不符的地方。差异集中在文末。

> 2026-10-20 追加：设计 `002-weekly.md` 已加入本目录，已合入 `main`。002 的决定和任务状态见第 9 节；第 1–8 节仍是对 `main` @ `021951d` 的复核记录，未按 002 重写。

## 1. 项目目标

阿森纳足球俱乐部中文每日简报站点（「阿森纳日报」）：赛程、伤病、官方消息；转会与媒体侧写标明是否官方。非官方站点。

- 仓库：https://github.com/negiii0729/arsenal-daily（public，默认分支 `main`）
- 站点：https://negiii0729.github.io/arsenal-daily/（复核时 HTTP 200）
- 两期日报页面均为 HTTP 200：
  - https://negiii0729.github.io/arsenal-daily/Daily/2026-10-17-阿森纳日报/
  - https://negiii0729.github.io/arsenal-daily/Daily/2026-10-18-阿森纳日报/
- 线上首页和归档 HTML 都包含 `2026-10-17` 与 `2026-10-18`。Pages API：`build_type` 为 `workflow`，公开站点，强制 HTTPS。

## 2. 技术栈

- `requirements.txt` 三行，都没有钉死补丁版本：
  - `mkdocs>=1.6,<2`（有上界，没有钉到具体版本）
  - `mkdocs-material>=9.5`（只有下界）
  - `pyyaml`（完全未指定版本）
- 最近一次成功部署（Actions run #5，`39081864429`）实际装到的直接依赖：`mkdocs==1.6.1`、`mkdocs-material==9.7.7`、`PyYAML==6.0.3`。本地用同一份 `requirements.txt` 安装，得到相同的三个版本。
- 传递依赖会漂。run #1 装到 `platformdirs==4.13.3`，run #5 装到 `platformdirs==4.13.4`。直接依赖版本这两次相同。
- 主题：Material，`language: zh`，浅色 / 深色跟随系统，正文字体 Noto Sans SC，代码字体 Roboto Mono。自定义样式 `docs/stylesheets/extra.css` 为 287 行。
- 构建钩子：`hooks/autonav.py`。
- CI/CD：`.github/workflows/deploy.yml`，`actions/setup-python` 使用 Python 3.12。run #1 的日志里解释器是 Python 3.12.15。
- 构建日志里有 Material 团队关于 MkDocs 2.0 的横幅（stderr）。它对 `mkdocs build --strict` 的退出码没有影响：当前站点 `--strict` 退出码为 0。

## 3. 目录结构

`main` @ `021951d` 的全部跟踪文件：

```
.github/workflows/deploy.yml   # 仅此一个工作流：构建 + 部署 Pages
mkdocs.yml                     # 未写 nav；nav 由钩子在 on_config 写入
hooks/autonav.py
docs/index.md                  # 已提交的首页，内容落后于日报
docs/Daily/index.md            # 已提交的归档，同样落后
docs/Daily/2026-10-17-阿森纳日报.md
docs/Daily/2026-10-18-阿森纳日报.md
docs/stylesheets/extra.css
requirements.txt
README.md
.gitignore                     # 只忽略 site/、__pycache__/、*.pyc、.venv/
```

没有 `design/`、没有测试、没有第二份工作流、没有 issue（`gh issue list --state all` 为空）。仓库 rulesets 列表为空。读取 classic branch protection 时，当前 token 得到 403，因此不能断定「完全没有分支保护」；能断定的是下面两次对 `main` 的直接更新没有被拒绝。

## 4. 构建 / 部署

触发：push 到 `main`，或手动 `workflow_dispatch`。没有 `pull_request` 触发器。

步骤：`actions/checkout@v4` → `actions/setup-python@v5`（Python 3.12）→ `pip install -r requirements.txt` → `mkdocs build`（没有 `--strict`）→ `actions/configure-pages@v5`（`enablement: true`）→ `actions/upload-pages-artifact@v3`（`site/`）→ `actions/deploy-pages@v4`。

权限：`contents: read`、`pages: write`、`id-token: write`。并发组 `pages`，`cancel-in-progress: true`。`deploy` 依赖 `build`，构建失败不会进入部署。两次失败都发生在第一次成功部署之前，所以仓库历史上还没有「已有线上版本、随后构建失败、旧版本保留」的实测记录；工作流结构本身是这样。

`hooks/autonav.py` 在 `on_config` 中扫描 `docs/Daily/*.md`（跳过 `index.md`）：

- frontmatter 用正则取出，再用 `yaml.safe_load`。解析抛错时 `except Exception` 后变成空 dict，不打日志。
- `title` 缺失时用正文第一个 `#` 标题，再退回文件名（去掉扩展名）。
- `date` 若是 `datetime` / `date` 会格式化。缺失时从文件名提取 `\d{4}-\d{2}-\d{2}`，再没有才用文件 mtime 的日期。
- 按日期字符串、文件名倒序。导航、归档包含全部日报；首页最多 `LATEST_N = 30` 条。
- 每次构建覆盖 `docs/index.md` 和 `docs/Daily/index.md`，内容相同则不写。文件不存在时也会创建。已在删除这两个文件的副本上验证：`mkdocs build --strict` 退出码 0，并重新写出首页，且 `site/index.html` 含 10-18 那期。

两期已提交日报都有合法 frontmatter（`title` 与 `date: 2026-10-17` / `date: 2026-10-18`）。缺字段、坏 YAML 的路径目前没有被真实日报触发。

本地预览命令与 README 一致：`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && mkdocs serve`，然后打开 http://127.0.0.1:8000/ 。

### Actions 运行记录

工作流名都是 “Deploy MkDocs to Pages”，事件都是 `push`。

| # | run id | 时间 (UTC) | UTC+8 | 提交 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 1 | [39048939542](https://github.com/negiii0729/arsenal-daily/actions/runs/39048939542) | 2026-10-17 16:20:00 | 10-18 00:20 | `e07e9e8` | failure |
| 2 | [39049167964](https://github.com/negiii0729/arsenal-daily/actions/runs/39049167964) | 2026-10-17 16:23:06 | 10-18 00:23 | `06aae0b` | failure |
| 3 | [39049437091](https://github.com/negiii0729/arsenal-daily/actions/runs/39049437091) | 2026-10-17 16:26:49 | 10-18 00:26 | `b8407b6` | success |
| 4 | [39052350738](https://github.com/negiii0729/arsenal-daily/actions/runs/39052350738) | 2026-10-17 17:07:12 | 10-18 01:07 | `f9955f7` | success |
| 5 | [39081864429](https://github.com/negiii0729/arsenal-daily/actions/runs/39081864429) | 2026-10-18 00:11:47 | 10-18 08:11 | `021951d` | success |

失败原因已经从日志确认，两次都不是 `mkdocs build` 失败（构建日志都是 `Documentation built`）：

- **#1**：当时的工作流还没有 `enablement: true`（日志里该参数为 `false`）。`configure-pages` 报错：`Get Pages site failed ... Error: Not Found`，并提示仓库未启用 Pages，或考虑 `enablement` 参数。
- **#2**：PR #2 已经把 `enablement: true` 合并进来。`mkdocs build` 仍然成功。`configure-pages` 先警告 `Get Pages site failed ... Not Found`，然后失败：`Create Pages site failed. Error: Resource not accessible by integration`。也就是 token 无权创建 Pages 站点。
- **#3 才恢复**。提交 `b8407b6`（说明 “Retrigger Pages deploy”）是空提交，相对 `06aae0b` 没有文件变化，工作流内容与失败的 #2 相同。这次 `configure-pages` 通过并设置了 `GITHUB_PAGES=true`，随后部署成功。因此恢复发生在仓库文件之外（Pages 站点变得可用，或创建权限变得可用）。日志不能区分是哪一种。原稿把恢复归到 “Enable GitHub Pages on first configure-pages run” 那次提交，与日志不符：那次提交对应的就是失败的 #2。

同几次构建里还有 Actions 提示：`actions/checkout@v4`、`actions/setup-python@v5`、`actions/configure-pages@v5` 面向 Node.js 20，运行器把它们转到 Node.js 24。这没有导致失败。

### `mkdocs build` 与 `--strict` 的实际行为

在与 run #5 相同的依赖版本上，用当前 `main` 的副本验证：

| 输入 | `mkdocs build` | `mkdocs build --strict` |
| --- | --- | --- |
| 当前两期日报 | 退出码 0 | 退出码 0 |
| 日报缺少 frontmatter，或 frontmatter YAML 无法解析 | 退出码 0，无 WARNING | 退出码 0，无 WARNING |
| 站内链接指向不存在的文档 | 退出码 0，有 MkDocs `WARNING`（点名源文件和目标） | 退出码 1，stdout 含 `Aborted with … warnings in strict mode!` |
| 外部链接 `https://example.invalid/nope` | 未测非 strict | 退出码 0，无该 URL 的 WARNING |

结论：工作流没有用 `--strict`，所以站内坏链接只警告、不让部署失败。钩子对 frontmatter 问题连警告都没有。`--strict` 不检查外部 URL。Material 的 MkDocs 2.0 横幅不是 MkDocs warning，不会单独把 `--strict` 打红。

## 5. 数据来源与内容生产流程

正文是仓库外写成的 Markdown。两期日报的来源包括 arsenal.com、premierleague.com、BBC、Telegraph、football.london，以及 X 帖子（正文写了曝光 / 点赞数）。要闻带来源链接。转会段自行标注「谣言 / 非官方」。文末写明 Inoreader 尚未接入。

仓库内没有抓取脚本、生成日报的代码或定时工作流。只有 Pages 部署。

提交方式，按 `main` 上的历史：

| 提交 | 作者 | 如何进入 `main` | 内容 |
| --- | --- | --- | --- |
| `e07e9e8` | squash，作者记为 negiii0729，Co-authored-by Cursor Agent | PR [#1](https://github.com/negiii0729/arsenal-daily/pull/1) squash merge | 站点骨架 + 10-17 日报 |
| `06aae0b` | squash，同上 | PR [#2](https://github.com/negiii0729/arsenal-daily/pull/2) squash merge | `configure-pages` 的 `enablement: true` |
| `b8407b6` | Cursor Agent | 直接提交到 `main`（空提交，父提交即 `06aae0b`） | 重跑 Pages 部署 |
| `f9955f7` | cursor[bot] merge | PR [#3](https://github.com/negiii0729/arsenal-daily/pull/3) merge commit | 主题与首页卡片 |
| `021951d` | Cursor Agent | 直接提交到 `main`（父提交 `f9955f7`，不是 merge commit） | 只新增 10-18 日报那一个文件 |

主题改版确实走了 PR #3。站点初版和 Pages 开关也走了 PR。直接写 `main` 的是空提交 `b8407b6` 和 10-18 日报 `021951d`。`021951d` 没有更新 `docs/index.md` 或 `docs/Daily/index.md`。

## 6. 当前问题与风险

1. **日报可以直推 `main` 并立刻部署。** `021951d` 已发生。没有 PR 检查。部署工作流只在 push `main` 时构建。构建硬失败时不会发布新版本；警告（包括站内坏链接）仍会发布。
2. **部署构建没有 `--strict`。** 站内坏链接在非 strict 下只产生 WARNING，退出码 0。已测的 `--strict` 不报告外部 URL（非 strict 未再单独测；MkDocs 默认把绝对链接记为 info，不会让构建失败）。frontmatter 缺失或 YAML 解析失败时钩子静默回退，`--strict` 也不会失败。原稿写「frontmatter 错误只产生警告；无链接检查」不准确。
3. **直接依赖未钉版本，传递依赖已漂过。** 见第 2 节。`mkdocs` 有 `<2` 上界，另外两个直接依赖没有上界。
4. **已提交的生成页是旧的。** `docs/index.md` 和 `docs/Daily/index.md` 只列出 10-17。钩子在构建时会补上 10-18（已用 diff 核对）。线上站点已经含两期，阅读站点的人不受影响。阅读仓库里这两个文件的人会以为没有 10-18。本地 `mkdocs build` 会改写这两个文件，产生 diff。`.gitignore` 没有忽略它们。
5. **钩子的日期回退在 CI 里不可靠。** 文件名里没有 `YYYY-MM-DD`、frontmatter 也没有 `date` 时，用 `os.path.getmtime`。Actions checkout 之后 mtime 是检出时间，排序会跟着构建日走。YAML 合法但不是 mapping（例如一块列表）时，`meta.get` 抛出 `AttributeError`，当前的 `except` 包不住这一步，`mkdocs build` 以 traceback 退出码 1 结束。缺字段和 YAML 语法错误则是另一条路径：静默回退，退出码 0。
6. **内容时效。** 正文引用 X 热度和媒体报道，链接以后可能失效，而 `--strict` 不检查外链。版权行和 README 写了非官方；仓库里没有更正或撤回流程。
7. **`main` 上没有测试、没有 issue、没有设计文档。** 本目录随设计 PR 新增，合入 `main` 之前仍然如此。

## 7. 建议的下一步

范围只包括下面四项，展开在 `design/001-publishing-pipeline.md`：

- 日报改走分支 + PR；PR 上用独立工作流跑 `mkdocs build --strict`。部署工作流保持现状。自动合并是否打开，留给 negi。
- 在 `requirements.txt` 把直接依赖钉成 run #5 的版本。
- 生成的 `docs/index.md`、`docs/Daily/index.md` 停止入库（gitignore 并从 Git 删除），不采用「CI 对比已提交副本」的做法。理由见设计文档。
- 日报必填 frontmatter `title` 和 `date`。钩子用 MkDocs 的 plugin logger 发 warning，使 `--strict` 失败。

不在下一步里做的：外部链接检查、更正 / 撤回机制、把部署命令改成 `--strict`、处理 Node 20 弃用提示。

## 8. 与原稿的差异

| 原稿 | 复核后 |
| --- | --- |
| `extra.css`「约 287 行」 | 正好 287 行 |
| 「版本未锁定」，并强调 material 只有下界 | `mkdocs` 另有 `<2` 上界。三个直接依赖都没钉补丁版本。传递依赖 `platformdirs` 已从 4.13.3 漂到 4.13.4 |
| #1、#2 失败原因「推测为首次启用 Pages，待确认」 | 已确认，且两次原因不同。#1 是 Pages 不存在且 `enablement: false`。#2 是 `enablement: true` 之后创建站点返回 403 `Resource not accessible by integration`。两次 `mkdocs build` 都成功 |
| 提交 “Enable GitHub Pages…” 之后恢复 | 该提交就是失败的 #2。恢复的是下一次空提交 `b8407b6`（run #3），工作流文件与 #2 相同 |
| 「10-18 由 Cursor Agent 直接 push；主题改版走过 PR #3」 | 这两句成立。补充：初版站点是 PR #1（squash），`enablement` 是 PR #2（squash）。另有一次 Cursor Agent 对 `main` 的空提交 `b8407b6` |
| 「坏链接、frontmatter 错误只产生警告；无链接检查」 | 站内坏链接：非 strict 为 WARNING 且退出码 0，`--strict` 退出码 1。frontmatter 缺失和 YAML 解析失败：钩子静默，`--strict` 仍为 0。外部链接：`--strict` 不报 |
| 已提交 index 落后「不影响站点」 | 成立，并已用线上 HTML 核对：首页和归档都有 10-17 与 10-18 |
| 失败时保留旧版本 | 工作流结构如此（`deploy` 依赖 `build`）。仅有的两次失败发生在第一次成功部署之前，没有「覆盖失败后留下旧站」的实测 |
| 文末 Codex 调用记录（`codex exec` 403、workspace routing） | 本次复核没有重跑 Codex。那段记录只作为原稿附录，不作为仓库事实 |

原稿附录（未复核，不作为仓库事实）：起草时 `codex exec -m gpt-6-astra`（codex-cli 0.163.0，登录状态为 ChatGPT）失败，`https://chatgpt.com/backend-api/codex/models` 返回 403，随后 `workspace routing discovery failed`。

## 9. 设计 002：日报改周报（已上线）

设计文档：`design/002-weekly.md`（编号 `002`）。

**改版决定：** 站点从每日简报改为每周简报。每周一 **08:00（Asia/Shanghai）** 发布一期，覆盖发布日前一周的周一至周日；首期为 **2026-10-26，第 1 期**，覆盖 **2026-10-19～2026-10-25**。新周报使用 `docs/Weekly/YYYY-MM-DD-阿森纳周报.md`；已有 4 篇日报原地保留为停更存档，不移动、不改 URL；三个 `index.md` 由 `hooks/autonav.py` 生成，不手改。仓库名、Pages 地址、CI 名称 **Check MkDocs build**（`mkdocs build --strict`）和现有自动 squash 合并机制保持不变。

### AW-01：周报自动导航、校验与站点文案

- 状态：**PR [#14](https://github.com/negiii0729/arsenal-daily/pull/14)（`aw-01-weekly-nav`）已 squash 合入 main（6a66dbf）。**
- 本地验证（`mkdocs build --strict`）：第 1–3、5、6、8 项按预期通过（无周报兜底文案、首期与第 2 期排序和导航、两种日期写法、省略 `summary`、旧日报未改动、清理临时周报后重建成功）；第 4 项及第 5 项中的非法 `summary` 均按预期构建失败，日志定位文件与原因，无未捕获异常。第 7 项不适用：仓库中没有兜底首期，未执行迁移。CI（Check MkDocs build）通过。

### AW-02：周报投稿规范与状态更新

- 状态：**PR [#15](https://github.com/negiii0729/arsenal-daily/pull/15)（`aw-02-weekly-docs`）已 squash 合入 main（e642259）。**
- 内容：按 002 更新 `README.md` 的周报发布节奏、文件名、全部 frontmatter 规则与完整示例、`weekly/YYYY-MM-DD` 分支、`Add 第N期 阿森纳周报 YYYY-MM-DD` PR 标题、自动 squash 合并、旧日报存档、生成索引不可手改及首期兜底迁移规则；同步更新本节。

**上线状态：** AW-01、AW-02 均已合入 `main`（#14 `6a66dbf`、#15 `e642259`）；线上 Deploy run `39378718020` 已上线，QA L3 PASS。
