# 阿森纳周报

阿森纳足球俱乐部中文每周简报。站点用 MkDocs Material 构建，经 Pull Request 合并到 `main` 后由 GitHub Actions 发布到 GitHub Pages。

**Pages：** https://negiii0729.github.io/arsenal-daily/

**仓库：** https://github.com/negiii0729/arsenal-daily

内容整理自公开来源（以 arsenal.com 为准，转会与媒体侧写会标明是否官方），不是阿森纳官方站点。

## 发布节奏

- 每周一 **08:00（Asia/Shanghai）** 发布一期，覆盖发布日前一周的周一至周日。
- 首期为 **2026-10-26，第 1 期**，覆盖 **2026-10-19～2026-10-25**。
- 发布时间是运营约定；仓库没有定时发布或定时开 PR 的工作流。

## 目录

- `docs/Weekly/YYYY-MM-DD-阿森纳周报.md` — 周报。文件名日期为发布当天的周一，必须与 frontmatter 的 `date` 一致。
- `docs/Daily/YYYY-MM-DD-阿森纳日报.md` — 2026-10 改版前的日报，已停更，原地保留作为冻结存档。
- `hooks/autonav.py` — 构建时扫描 `docs/Weekly` 和 `docs/Daily`，校验周报字段，生成导航和三个索引页。新增周报不用改 `mkdocs.yml`。
- `docs/index.md`、`docs/Weekly/index.md`、`docs/Daily/index.md` — 钩子在构建时生成，不入库，不要手改。
- `.github/workflows/ci.yml` — 对 base 为 `main` 的 PR 做严格构建。工作流 **Check MkDocs build**，job **mkdocs build --strict**，检查命令为 `mkdocs build --strict`。
- `.github/workflows/deploy.yml` — `main` 更新（以及手动触发）时 `mkdocs build`，并把 `site/` 部署到 GitHub Pages。

## 本地预览

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

浏览器打开 http://127.0.0.1:8000/ 。

## 周报文件名

固定为 `docs/Weekly/YYYY-MM-DD-阿森纳周报.md`，日期为**发布当天的周一**，必须与 frontmatter `date` 一致。扫描 `Weekly/`、`Daily/` 时排除 `index.md`。`Weekly/` 不存在时由钩子创建；没有周报文件是正常状态。

## frontmatter 规范

周报必须满足下表；日报继续使用原有的 `title`、`date` 规则，不要求补充周报字段。

| 字段 | 必填 | 规则 |
|---|---|---|
| `title` | 是 | 字符串，格式为 `阿森纳周报 · 第N期 · MM.DD–MM.DD`；期号对应 `issue`，区间对应 `week_start`、`week_end` |
| `date` | 是 | 发布日，真实有效的 `YYYY-MM-DD` 日期，必须为周一且与文件名日期一致 |
| `issue` | 是 | 正整数，首期为 `1`；拒绝布尔值、字符串、浮点数、零及负数 |
| `week_start` | 是 | `YYYY-MM-DD`，必须为 `date - 7 天`，即上周一 |
| `week_end` | 是 | `YYYY-MM-DD`，必须为 `date - 1 天`，即上周日 |
| `summary` | 否 | 一句话字符串；本次不要求在卡片展示 |

标题区间使用 **en dash `–`**，月份和日期均为两位；跨年区间按两个日期各自的月日显示。

三个日期字段允许 YAML 解析出的纯 `datetime.date`，或严格符合 `YYYY-MM-DD` 且可解析的字符串；拒绝带时间的 `datetime.datetime` 和不存在的日期。提供 `summary` 时须为非空单行字符串；省略不告警。

格式错误、必填字段缺失或 YAML 无法解析时，钩子用 MkDocs 插件 logger 输出 `warning`，包含仓库相对路径、字段名和原因，`mkdocs build --strict` 因此失败。无效周报会被跳过，不参与首页、归档及导航生成。

### 完整示例

文件：`docs/Weekly/2026-10-26-阿森纳周报.md`

```markdown
---
title: "阿森纳周报 · 第1期 · 10.19–10.25"
date: "2026-10-26"
issue: 1
week_start: "2026-10-19"
week_end: "2026-10-25"
summary: "汇总本周阿森纳赛程、伤病与官方消息。"
---

# 阿森纳周报 · 第1期 · 10.19–10.25

## 本周概览

填写经核实的本周内容。
```

## 开一期周报

不要把周报直接 push 到 `main`。从最新的 `main` 建分支，只新增一篇周报，开 PR。一期一个 PR。正常投稿流程只使用 Weekly 路径。

1. 从最新的 `origin/main` 建分支，分支名用 `weekly/YYYY-MM-DD`。PR 的 base 是 `main`。
2. 只新增 `docs/Weekly/YYYY-MM-DD-阿森纳周报.md`，按上面的完整示例写 frontmatter。不改 `mkdocs.yml`，不手改 `docs/index.md`、`docs/Weekly/index.md` 和 `docs/Daily/index.md`。
3. 推送分支，用 `gh pr create --base main` 开 PR。标题用 `Add 第N期 阿森纳周报 YYYY-MM-DD`。
4. 开 PR 时用 `gh pr merge --auto --squash` 开启自动合并。**Check MkDocs build**（job **mkdocs build --strict**）通过后自动 squash 合并上线。检查失败则 PR 不会合并、网站不更新；周报产出方要自己查看 PR 状态（可用 `gh pr checks` / `gh pr view`），失败时修复或告诉架构师。

```bash
git fetch origin main
git checkout -b weekly/2026-10-26 origin/main
# 写入 docs/Weekly/2026-10-26-阿森纳周报.md
git add docs/Weekly/2026-10-26-阿森纳周报.md
git commit -m "Add 第1期 阿森纳周报 2026-10-26"
git push -u origin HEAD
gh pr create --base main --title "Add 第1期 阿森纳周报 2026-10-26" --body "本期周报。"
gh pr merge --auto --squash
```

## 旧日报（仅历史与兜底）

`docs/Daily/` 下 2026-10-17 至 2026-10-20 的 4 篇日报是停更存档：不移动、不重命名、不改写，原有 URL 保持不变。日报归档页标题为“日报存档”，说明为“2026-10 改版前的每日简报，已停更”。正常周报流程不再新增日报。

若 2026-10-26 前改版未上线，首期仍在 `docs/Daily/` 按旧文件名和旧 frontmatter 格式发布。改版上线后，由开发将该篇迁移至：

```text
docs/Weekly/2026-10-26-阿森纳周报.md
```

补齐周报字段，并保持正文内容。该兜底首期是新页，其迁移不算破坏 URL；不迁移已有 4 篇日报。

合并进 `main` 后，Actions 工作流 “Deploy MkDocs to Pages” 会构建并部署。仓库需在 Settings → Pages 中把 Source 设为 **GitHub Actions**（首次启用 Pages 时选一次即可）。
