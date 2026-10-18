# 001 日报发布走 PR，并加上构建检查

状态文档：`design/STATUS.md`（复核对象 `main` @ `021951d`）。

## 目标

一期日报从写完到出现在 https://negiii0729.github.io/arsenal-daily/ ，中间经过分支和 Pull Request。合并前要先通过 `mkdocs build --strict`；日报缺字段或站内链接断裂时，这次构建失败，PR 不能当绿检查合并。

具体要达到：

- 仓库外的产出代理不再把日报直接 push 到 `main`。它开 PR，PR 的检查是 `mkdocs build --strict`。
- 这个检查和现有的 Pages 部署工作流分开。部署仍只在 `main` 更新之后发生。
- `requirements.txt` 的直接依赖钉到当前线上正在使用的版本，避免未声明的升级改掉站点。
- 仓库里那两份过期的生成页不再充当源文件。
- 每期日报的 frontmatter 必须有 `title` 和 `date`。缺了，严格构建失败。

自动合并（检查变绿就合并，不必 negi 点一下）是可选项，本文不替 negi 打开。见文末待决问题。

## 范围（含不做的事）

做的事只有五块，对应文末 AD-01 到 AD-05，每块一个 PR：

1. 钉依赖版本。
2. 新增 PR 检查工作流。
3. 停止跟踪生成的首页和归档。
4. 钩子对缺失的 `title` / `date` 发出 MkDocs warning。
5. 在 README 写明产出代理怎么开 PR。

不做的事：

- 不修改已有日报正文、`docs/stylesheets/extra.css`、`mkdocs.yml` 的主题和插件。
- 不把 `.github/workflows/deploy.yml` 的 `mkdocs build` 改成 `--strict`，不改它的触发器、权限、并发组或 `enablement`。PR 检查变红时，已发布的站点保持不动；只有合进 `main` 之后，现有部署工作流才发布。
- 不加外部链接检查。已验证：日报里放 `https://example.invalid/nope` 时，`mkdocs build --strict` 退出码仍为 0。站内指向不存在文档的链接，`--strict` 会失败，这是 MkDocs 自带行为，检查工作流因此能拦住这类错误，不必再加工具。
- 不加更正 / 撤回流程、测试框架、抓取脚本、定时任务，也不接 Inoreader。
- 不处理 Actions 关于 Node.js 20 的弃用提示。
- 不在这些 PR 里修改 GitHub 仓库设置。ruleset 和 auto-merge 要等 negi 决定（文末）。

## 技术选型与理由

### 日报用分支 + PR

产出代理发布一期时按下面做。步骤保持少，一个人维护得过来。

1. 从最新的 `origin/main` 建分支。分支名用 `daily/YYYY-MM-DD`。若该代理自己的运行环境强制别的前缀（例如 `cursor/…`），用它被要求的前缀即可。要求只有两条：PR 的 base 是 `main`，并且不 push `main`。
2. 只新增 `docs/Daily/YYYY-MM-DD-阿森纳日报.md`。文首：

   ```yaml
   ---
   title: 阿森纳日报 · YYYY-MM-DD
   date: YYYY-MM-DD
   ---
   ```

   `date` 写成 YAML 日期或 `YYYY-MM-DD` 字符串都可以。现有两期已经是这种写法。
3. 不改 `mkdocs.yml`。不手改首页和归档。AD-03 之后这两个文件被忽略，提交它们没有意义。
4. 推送分支并开 PR。标题用 `Add YYYY-MM-DD 阿森纳日报`。一期一个 PR。
5. 等检查通过。合并用 squash，与已合并的 PR #1、PR #2 一致。主题那次 PR #3 是 merge commit；日报不必沿用。

命令形状：

```bash
git fetch origin main
git checkout -b daily/2026-10-19 origin/main
# 写入 docs/Daily/2026-10-19-阿森纳日报.md
git add docs/Daily/2026-10-19-阿森纳日报.md
git commit -m "Add 2026-10-19 阿森纳日报"
git push -u origin HEAD
gh pr create --base main --title "Add 2026-10-19 阿森纳日报" --body "本期日报。"
```

谁来点合并，见文末第一个待决问题。在 negi 启用 main 的规则之前，上述步骤是约定：`021951d` 证明当前身份可以直接 push `main`。README 写清楚步骤，规则才能有东西可要求。

### PR 检查与部署分开

新增 `.github/workflows/ci.yml`，不要把检查塞进 `deploy.yml`。

- 触发：`pull_request` 且 base 为 `main`。不在 push `main` 时再跑一遍，避免和部署重复构建。
- 权限只有 `contents: read`。不声明 `pages: write` 或 `id-token: write`，PR 跑不到部署用的 token 权限。
- 步骤与部署的构建段对齐：`actions/checkout@v4`、`actions/setup-python@v5` 的 Python 3.12、`pip install -r requirements.txt`、然后 `mkdocs build --strict`。
- 工作流名：`Check MkDocs build`。job 名：`mkdocs build --strict`。以后若把该检查设为必需状态检查，名称用 job 名。

当前 `main` 的内容跑 `mkdocs build --strict` 退出码为 0（依赖版本与 Actions run #5 相同）。stderr 上的 Material / MkDocs 2.0 横幅会照常出现，它不是失败条件。

站内坏链接已经会让这条命令退出码为 1。缺 frontmatter 要等 AD-04 才会失败。

### 在 `requirements.txt` 钉直接依赖

钉成 run #5（`39081864429`，`main` @ `021951d`，2026-10-18）装到的版本，本地用同一文件安装得到的也是这三行：

```text
mkdocs==1.6.1
mkdocs-material==9.7.7
PyYAML==6.0.3
```

用 `==` 写在 `requirements.txt`，不加 constraints 文件，不引入 pip-tools。直接依赖只有三个，升级时改这三行并让严格构建通过即可。

`mkdocs` 现在的 `>=1.6,<2` 挡得住 2.x，挡不住 1.6 里的小版本。Material 只有下界。钉到 1.6.1 也避开构建日志里那则 MkDocs 2.0 横幅所讲的不兼容框架。

不冻结整棵传递依赖树。run #1 到 run #5 之间 `platformdirs` 从 4.13.3 变成 4.13.4，直接依赖没变，站点构建仍成功。完整锁文件能消掉这种漂移，但每次升级都要重写锁文件，对这个站点过重。接受传递依赖仍可能变；直接依赖不再变，除非有人改 `requirements.txt`。

### 生成的首页和归档：停止入库

推荐：把 `docs/index.md` 和 `docs/Daily/index.md` 从 Git 删除，并写入 `.gitignore`。

理由：

- 这两个文件是 `on_config` 的输出。钩子文件头已写明每次构建覆盖、不要手改。源是 `docs/Daily` 里除 `index.md` 以外的日报。
- 落后已经发生。`021951d` 只加了 10-18 的正文，两份已提交 index 仍只有 10-17。本地构建会把 10-18 写回去，工作区出现 diff。
- 站点不读仓库里的旧副本。部署时钩子重写它们。线上首页和归档现在就同时有 10-17 和 10-18。删除已提交副本不改变线上结果。
- 在删掉这两个文件的副本上，`mkdocs build --strict` 退出码为 0，钩子会重新创建它们，`site/index.html` 含 10-18。`navigation.indexes` 用的 `Daily/index.md` 也在同一次 `on_config` 里写好，构建读得到。
- 若改成 CI 一致性检查（构建后 `git diff --exit-code -- docs/index.md docs/Daily/index.md`），每期 PR 都必须提交这两份生成结果。产出代理已经漏过一次。检查会红，然后多一轮「构建、把生成文件加进同一个 PR」。一个人维护的日报不值得这个步骤。GitHub 上浏览仓库的人也不是站点读者；README 会说明首页和归档只在构建时出现，站点地址仍是 Pages。

`.gitignore` 只写这两条路径，不用 `docs/**/index.md`，避免把以后真正手写的 index 一起忽略。

### 必填 frontmatter，并用 MkDocs warning 让 `--strict` 失败

改 `hooks/autonav.py` 的 `_meta`，仍保留「缺了也能拼出一页」的回退，这样不带 `--strict` 的部署命令行为不变：页面还在，只是日志里有 WARNING。PR 检查带 `--strict`，同一条 WARNING 会失败。

实现要点：

- 使用 `mkdocs.plugins.get_plugin_logger`。已在临时副本验证：`log.warning` 的内容会出现在 stderr，形如 `WARNING - hooks/autonav: <路径>: …`；`mkdocs build --strict` 退出码 1，stdout 含 `Aborted with N warnings in strict mode!`；去掉 `--strict` 时退出码 0，WARNING 仍在。`print` 或标准库 `warnings.warn` 不会被 `--strict` 计为失败，不要用。
- 没有 frontmatter、YAML 解析失败、或解析结果不是 dict：打 warning，点明文件路径，并把 `title`、`date` 视为缺失。不是 dict 时，现在的钩子会在 `meta.get` 抛出 `AttributeError`，整个构建退出码 1，没有 WARNING。改完之后，非 strict 构建仍能完成，部署不会再被这条 traceback 打断；`--strict` 则因为 warning 失败。PR 检查负责拦住。
- `title` 缺失或空字符串：warning 点明路径和 `title`，然后保持现有回退（第一个 `#` 标题，否则文件名）。
- `date` 缺失，或既不是 `datetime.date` / `datetime.datetime`、也不是 `YYYY-MM-DD` 字符串：warning 点明路径和 `date`。文件名里有日期则继续用文件名。文件名里也没有时，排序键用 `0000-00-00`，不再调用 `os.path.getmtime`。mtime 在 Actions checkout 之后是检出时间，同一文件两次构建可能排到不同的「今天」。`0000-00-00` 在现有倒序里稳定地排在最后。
- 现有两期都有 `title` 和 `date`，严格构建应保持退出码 0，且日志里没有「缺少 frontmatter」。
- 警告文案用中文，与钩子「Chinese-only」一致，并带仓库内相对路径，方便在 Actions 日志里点到文件。

部署工作流仍是 `mkdocs build`。有人绕过 PR 把缺 frontmatter 的文件推进 `main` 时，部署会成功并留下 WARNING。要让这种情况进不了 `main`，需要文末的 ruleset，不是再改部署命令。

## 目录 / 文件改动

| 任务 | 文件 | 改动 |
| --- | --- | --- |
| AD-01 | `requirements.txt` | 三行改为 `mkdocs==1.6.1`、`mkdocs-material==9.7.7`、`PyYAML==6.0.3`。可加一行注释，注明版本来自 Actions run `39081864429` |
| AD-02 | `.github/workflows/ci.yml`（新文件） | PR 检查。不改 `deploy.yml` |
| AD-03 | `.gitignore`；删除 `docs/index.md`、`docs/Daily/index.md` | 忽略并 `git rm` 这两份生成页 |
| AD-04 | `hooks/autonav.py` | 缺 `title` / `date`、坏 YAML、非 dict 的 frontmatter 打 MkDocs warning；无日期时不再用 mtime |
| AD-05 | `README.md` | 写出分支、PR、frontmatter 示例、不要直推 `main`、不要手改两份 index、检查名称 |

AD-01 到 AD-04 的文件互不重叠，可以并行开 PR。AD-05 改 README，放在最后，避免文档先于行为落地。

## 拆好的任务清单

### AD-01 钉住直接依赖

把 `requirements.txt` 的三行改成上一节的精确版本。

- 文件：`requirements.txt`
- 依赖：无

验收标准：

1. 文件中 `mkdocs`、`mkdocs-material`、`PyYAML` 三行都是 `==`，不再出现 `>=` 或 `<`。没有第二份 constraints / lock 文件。
2. 新建虚拟环境后执行 `pip install -r requirements.txt`。`pip show mkdocs mkdocs-material PyYAML` 的 Version 分别为 `1.6.1`、`9.7.7`、`6.0.3`。
3. 在仓库根目录执行 `mkdocs build`，退出码 0，生成 `site/index.html`。
4. 该 PR 不修改工作流、钩子、日报和样式。

### AD-02 增加与部署分离的 PR 检查

新增只在 PR 上运行的严格构建。

- 文件：`.github/workflows/ci.yml`
- 依赖：无。若 AD-01 已在 `main`，本检查安装的就是钉住的版本；未合并时安装的仍是范围版本，检查本身仍然有效。

验收标准：

1. 对 `main` 开一个只含该工作流（或在其之上无内容错误）的 PR。Actions 出现工作流 **Check MkDocs build**，job **mkdocs build --strict** 为绿。日志中的命令是 `mkdocs build --strict`，Python 为 3.12。该 PR 上 **不会** 出现 “Deploy MkDocs to Pages”（`deploy.yml` 没有 `pull_request`）。
2. 另开一个不合并的试验 PR：在 `docs/Daily/` 放一篇 frontmatter 合法、但含站内死链接（指向同目录不存在的 `.md`）的日报。同一 job 为红，退出码非 0，日志含 MkDocs `WARNING` 以及找不到的目标路径，stdout 或日志含 `strict mode`。关闭该 PR，不合并。
3. 试验 PR 的工作流权限里没有 Pages 部署。YAML 中无 `pages: write`、无 `actions/deploy-pages`、无 `actions/upload-pages-artifact`。
4. `deploy.yml` 的 diff 为空。合入 AD-02 之后，下一次 push `main` 仍由 “Deploy MkDocs to Pages” 部署，https://negiii0729.github.io/arsenal-daily/ 返回 HTTP 200。

### AD-03 不再提交生成的首页和归档

生成页只留在构建过程里。

- 文件：`.gitignore`（追加两条）、`docs/index.md`（从 Git 删除）、`docs/Daily/index.md`（从 Git 删除）
- 依赖：无

验收标准：

1. `git ls-files docs/index.md docs/Daily/index.md` 无输出。`.gitignore` 含有这两条路径，且不含宽泛的 `docs/**/index.md`。
2. 在干净工作区执行 `mkdocs build --strict`，退出码 0。构建后这两个文件重新出现在工作区，`git status --short` 不列出它们。`site/index.html` 同时含 `2026-10-17` 和 `2026-10-18`。
3. PR diff 不含日报正文、钩子和工作流。
4. 合并进 `main` 且 “Deploy MkDocs to Pages” 成功之后，https://negiii0729.github.io/arsenal-daily/ 与 https://negiii0729.github.io/arsenal-daily/Daily/ 均 HTTP 200，HTML 中仍能找到 `2026-10-17` 和 `2026-10-18`。两期日报 URL 仍为 HTTP 200。

### AD-04 缺失 frontmatter 时让严格构建失败

钩子把缺字段变成 MkDocs warning。

- 文件：`hooks/autonav.py`
- 依赖：无。本地即可验收。AD-02 已在 `main` 时，用下面的坏文件开的试验 PR 应得到红检查。

验收标准：

1. 只保留现有两期日报时，`mkdocs build --strict` 退出码 0，日志中没有「缺少 frontmatter」。
2. 在副本或试验分支增加 `docs/Daily/2099-01-01-缺字段.md`，内容只有一行 `# 缺字段`，没有 frontmatter。`mkdocs build --strict` 退出码非 0；stderr 的 `WARNING` 含该文件路径以及 `title` 和 `date`；stdout 含 `Aborted with` 和 `strict mode`。同一工作区执行 `mkdocs build`（无 `--strict`）退出码 0，且仍打印上述 `WARNING`。构建产物里该页仍存在（回退标题来自 `#` 标题，日期来自文件名 `2099-01-01`）。
3. 把该文件的 frontmatter 改成无法解析的 YAML（例如 `title: [oops`，没有闭合）。`mkdocs build --strict` 退出码非 0，`WARNING` 含该文件路径。
4. 增加 `docs/Daily/无日期文件名.md`，frontmatter 只有 `title: 无日期文件名`。`mkdocs build --strict` 退出码非 0，`WARNING` 点明该文件和 `date`。连续构建两次（可用去掉 `--strict` 的命令，避免第一次失败时不好比较产物），第二次之前 `touch` 该文件。`docs/Daily/index.md` 里这一条的日期两次都是 `0000-00-00`，不随 mtime 变成当天。
5. 增加 `docs/Daily/2099-05-01-列表.md`，frontmatter 是 YAML 列表（例如只有 `- item`），不是 mapping。`mkdocs build` 退出码 0，日志是 `WARNING` 而不是 `AttributeError`。`mkdocs build --strict` 退出码非 0。
6. 合入 `main` 的 PR 不包含上述 `2099-*` 和 `无日期文件名.md`。合并后站点首页 HTTP 200，仍列出 10-17 与 10-18。

### AD-05 把开 PR 的步骤写进 README

让仓库外的产出代理按同一份说明操作。

- 文件：`README.md`
- 依赖：AD-02、AD-03、AD-04（文档里的检查名、gitignore 和 frontmatter 规则要和已落地的行为一致）

验收标准：

1. README 写明：日报不要直接 push `main`；从 `main` 建分支；只添加 `docs/Daily/YYYY-MM-DD-阿森纳日报.md`；给出 `title` 与 `date` 的 frontmatter 示例；用 `gh pr create --base main` 开 PR；合并方式写 squash；点名检查 **Check MkDocs build** / job **mkdocs build --strict**。
2. README 写明 `docs/index.md` 与 `docs/Daily/index.md` 由钩子在构建时生成、已不入库、不要手改。本地预览命令仍然是 `mkdocs serve`。
3. 按 README 的命令在试验分支加入一篇 frontmatter 完整、无站内死链的空日报（或真实日报），开向 `main` 的 PR。该 PR 上 job **mkdocs build --strict** 为绿。试验 PR 可随后关闭，不要求合并。
4. 该 PR 的 diff 只有 `README.md`。

## 待 negi 决定的问题

1. **检查变绿之后要不要自动合并？** 两种都能配合上面的流程。本文不预设。
   - 手动：检查绿了之后由 negi squash merge。产出代理停在开 PR。适合还想看一眼标题和「是否官方」标注的时候。
   - 自动：仓库打开 Allow auto-merge，并且第 2 点的必需检查已经生效。产出代理在 `gh pr create` 之后执行 `gh pr merge --auto --squash`。检查变绿后 GitHub 合并，现有 `deploy.yml` 再发布。不需要为自动合并再改代码。代价是：事实错误、没标清的传闻、失效的外链都会在构建通过后直接上线，因为 `--strict` 不审这些。
2. **要不要给 `main` 加 ruleset，把「走 PR」从约定变成限制？** 建议加，否则 AD-05 只是说明。规则：更新 `main` 必须通过 Pull Request；必需状态检查选 PR 页面上实际列出的那一项（工作流 `Check MkDocs build` 的 job 名是 `mkdocs build --strict`）；禁止 force push；negi 保留管理员绕过，给产出代理用的身份不绕过。仓库 rulesets 列表现在是空的；classic branch protection 这次读不到（403）。已经发生的直推是 `b8407b6` 和 `021951d`。这是仓库设置，不是 AD-01–AD-05 里的文件改动。自动合并只有在这条规则存在时才有门槛，否则绿检查可以被直推绕开。
