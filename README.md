# 阿森纳日报

阿森纳足球俱乐部中文每日简报。站点用 MkDocs Material 构建，经 Pull Request 合并到 `main` 后由 GitHub Actions 发布到 GitHub Pages。

**Pages：** https://negiii0729.github.io/arsenal-daily/

**仓库：** https://github.com/negiii0729/arsenal-daily

内容整理自公开来源（以 arsenal.com 为准，转会与媒体侧写会标明是否官方），不是阿森纳官方站点。

## 目录

- `docs/Daily/YYYY-MM-DD-阿森纳日报.md` — 每日报告。文首必须有 `title` 和 `date`。缺了会打 MkDocs warning，`mkdocs build --strict` 失败。
- `hooks/autonav.py` — 构建时扫描 `docs/Daily`，按日期新到旧生成导航。新增报告不用改 `mkdocs.yml`。
- `docs/index.md`、`docs/Daily/index.md` — 钩子在构建时生成，不入库，不要手改。
- `.github/workflows/ci.yml` — 对 base 为 `main` 的 PR 做严格构建。工作流 **Check MkDocs build**，job **mkdocs build --strict**。
- `.github/workflows/deploy.yml` — `main` 更新（以及手动触发）时 `mkdocs build`，并把 `site/` 部署到 GitHub Pages。

## 本地预览

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

浏览器打开 http://127.0.0.1:8000/ 。

## 开一期日报

不要把日报直接 push 到 `main`。从最新的 `main` 建分支，只新增一篇日报，开 PR。一期一个 PR。

1. 从最新的 `origin/main` 建分支。分支名用 `daily/YYYY-MM-DD`。运行环境若强制别的前缀（例如 `cursor/…`），用那个前缀。PR 的 base 是 `main`。
2. 只新增 `docs/Daily/YYYY-MM-DD-阿森纳日报.md`。不改 `mkdocs.yml`。不手改 `docs/index.md` 和 `docs/Daily/index.md`。文首：

   ```yaml
   ---
   title: 阿森纳日报 · YYYY-MM-DD
   date: YYYY-MM-DD
   ---
   ```

   `date` 写成 YAML 日期或 `YYYY-MM-DD` 字符串都可以。缺 `title` 或 `date` 时，**Check MkDocs build** 的 job **mkdocs build --strict** 失败。
3. 推送分支，用 `gh pr create --base main` 开 PR。标题用 `Add YYYY-MM-DD 阿森纳日报`。
4. 开 PR 时用 `gh pr merge --auto --squash` 开启自动合并。**Check MkDocs build**（job **mkdocs build --strict**）通过后自动合并上线；检查失败则不上线，并通知 negi / 架构师。

```bash
git fetch origin main
git checkout -b daily/2026-10-19 origin/main
# 写入 docs/Daily/2026-10-19-阿森纳日报.md
git add docs/Daily/2026-10-19-阿森纳日报.md
git commit -m "Add 2026-10-19 阿森纳日报"
git push -u origin HEAD
gh pr create --base main --title "Add 2026-10-19 阿森纳日报" --body "本期日报。"
gh pr merge --auto --squash
```

合并进 `main` 后，Actions 工作流 “Deploy MkDocs to Pages” 会构建并部署。仓库需在 Settings → Pages 中把 Source 设为 **GitHub Actions**（首次启用 Pages 时选一次即可）。
