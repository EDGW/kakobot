# 开发与打包

[返回 README](../README.md)

根目录只保留 AstrBot 发现入口，所有 Python 实现在 `src/`：

| 目录 | 职责 |
| --- | --- |
| `domain/` | 命令表、身份组、作用域、时间和参数规则 |
| `application/` | 运行时组装、统一鉴权/分发、用户会话协调 |
| `application/deadlines/` | DDL 创建、自动分析、解析、修改和提醒调度 |
| `application/roles/` | 本人身份查询和 Super 身份组管理 |
| `application/messaging/` | 广播与聊天总结 |
| `application/management/` | Super 申请审批和费用查询 |
| `infrastructure/storage/` | JSON/SQLite 基础存储、审计、申请、用量和启动迁移 |
| `infrastructure/storage/deadlines/` | DDL 任务、管理查询和个人默认提醒配置 |
| `infrastructure/storage/access/` | 身份组和只读群配置 |
| `infrastructure/storage/broadcasts/` | 广播接收会话、拒收偏好和更新文案读取 |
| `infrastructure/messaging/` | OneBot 收发、消息展开和输出分段/合并转发 |
| `infrastructure/model.py` | 模型请求与用量记录 |
| `presentation/` | 帮助、昵称/群名、费用和广播格式 |
| `presentation/deadlines/` | DDL 详情文字和本地卡片图片 |
| `adapters/` | AstrBot 生命周期与事件适配；申请订阅在终止时注销 |
| `tooling/` | 静态检查、图片示例和安装包构建 |

命令分发与鉴权共用 `domain/commands.py`，帮助正文以 `docs/commands/` 文档及其生成图片为准。管理 DDL 使用独立的明确授权入口，不放宽普通用户或 AI 修改任务的资源限制。角色批量修改原子替换 JSON；DDL 批量修改与调度共用锁，在一次事务内提交。

各层按职责建立子包，包入口仅说明用途，调用方直接导入实际模块。领域层只保留共享规则与值对象，不依赖应用、存储或展示实现。启动组装集中在 `application/runtime.py`，命令分发集中在 `application/dispatcher.py`。

默认广播内容保留在 `src/UPDATE.md`，由 `infrastructure/storage/broadcasts/updates.py` 每次读取。字体位于 `assets/fonts/`；移动渲染或读取模块时须同步校验资源定位。打包递归收集所有业务 Python 子包，并显式包含更新文案。

```sh
python -m src.tooling.check
ruff check src main.py
make publish
```

`make publish` 先生成文档图片，成功后再校验并制作插件安装包；图片生成失败时不继续打包。此命令仅本地构建，不上传、不创建 Release，也不执行 Git push。已生成图片后，可用 `python -m src.tooling.package` 单独打包；缺失所需帮助图片时打包失败并提示运行 make publish。

构建输出为 `dist/astrbot_plugin_kakobot-v版本.zip`，包含插件代码、README、Markdown 文档、中文字体、功能帮助 JPEG 和更新日志图片；不包含 README、configuration、development 的图片、examples、工具脚本、运行数据库、密钥或本地设计草稿。

命令文档中，一个 Markdown 文件对应一组功能，在每个命令下分别说明 CHAT、GROUP 的完整格式、所需权限组和行为。参数含义、默认值、作用范围、执行结果及示例直接写在对应命令下，不另设“使用规则与示例”汇总节。普通命令放在 `docs/commands/`，Super 命令放在 `docs/commands/super/`；各目录的 README 维护功能索引。

## 生成文档卡片图片

安装项目依赖后，在仓库根目录运行：

```sh
make docs
```

Makefile 默认使用 `python3`，需安装项目依赖。可用 `make docs PYTHON=.venv/bin/python` 指定解释器，或用 `make publish PYTHON="uv run --no-project --with Pillow python"` 在 uv 临时环境中构建；直接运行 `python -m src.tooling.docs_images` 也仍然支持。

脚本递归读取 `docs/` 下的功能 Markdown，跳过 README、configuration、development（文件名不区分大小写），每个功能文件生成 CHAT 和 GROUP 两张 JPEG。额外将根目录 `CHANGELOG.md` 生成独立的 `docs/pics/changelog.jpeg`，用于 `/changelog`，不按会话生成重复日志图片。输出到 `docs/pics/` 并保留源目录结构，例如 `docs/commands/ddl.md` 对应 `docs/pics/commands/ddl-chat.jpeg` 和 `docs/pics/commands/ddl-group.jpeg`。

标题以 `- CHAT` 或 `- GROUP` 结尾的段落只出现在对应会话图片中，整段内容及下级段落一同筛选。公共说明保留在两张图中；某个会话没有命令入口时显示不可用提示。没有会话标记的功能文档生成两份相同正文，页头分别标注会话类型。

排版使用随项目提供的中文字体：命令独立成卡片，行内命令高亮，代码块使用深色底，表格转为逐行信息卡。长命令和中文正文按实际文字宽度换行，图片高度随内容增长，不截断正文。超过 JPEG 高度上限时会报错，可减小字号或拆分源文档。

可以自定义输入、输出、宽度和正文字号：

```sh
make docs DOCS_ARGS="--docs docs --output docs/pics --width 1200 --font-size 25"
```

默认宽度1200像素、正文字号25像素。源目录中位于输出目录内的 Markdown 会跳过；重复运行覆盖同名图片，并移除 README、configuration、development 之前生成的图片，保留其他文件。`docs/pics/` 不加入 Git；发布安装包按当前功能文档清单包含对应 JPEG，不夹带过期页面。脚本只需 Pillow，不调用模型或网络。
## 图片帮助的运行链路

`application/messaging/help.py` 根据功能组和当前会话位置请求 `infrastructure/messaging/help_images.py` 读取安装目录下的 `docs/pics/commands/功能组-chat.jpeg` 或 `功能组-group.jpeg`；Super 页面位于同目录的 `super/` 子目录。未指定功能组时使用 help，`/super` 等同于 `/super help`。

普通帮助不动态筛选个人权限，文档图片说明具体入口的权限要求；Super 帮助在统一分发层鉴权后才读取图片。只接受单个功能组文件名，不提供任意路径读取。OneBot 使用原生 JPEG 图片消息发送到当前群或私聊，并继续经过出站和 Readonly 检查。原先的文字帮助渲染已移除。

标签发布工作流先安装 Pillow，再运行 `make publish`，确保干净检出也能生成并打包帮助图片。


`/changelog` 和 `/version` 在 CHAT、GROUP 均为 ANY 权限，由 `application/messaging/release.py` 处理。`infrastructure/messaging/release_info.py` 读取打包的日志图片或 metadata.yaml 版本；更新日志全文不硬编码到 Python 中。`make docs` 同时生成日志图片，`make publish` 将根目录 CHANGELOG.md、日志图片及功能帮助图片一并打包。自定义日志源可用 `DOCS_ARGS="--changelog /path/to/CHANGELOG.md"`。

## 更新日志与发布约定

未发布变更只写入 `CHANGELOG.md` 最前面的 `# Dev`，没有则新建。发布具体版本时将该 Dev 标题改为版本号；一旦条目有了版本号，其正文保持不变。修正、补充或后续行为变化都属于下一轮 Dev，不回写历史版本。

整理历史误写内容时，以发布标签内的 CHANGELOG.md 为基准，把发布后 commit 的变更摘到 Dev，并逐字核对已发布条目。当前已将 v1.3.0 发布后的新增说明从 v1.3.0 中摘出；v1.3.0 及更早正文与 v1.3.0 标签一致。发布工作流支持一级或二级版本标题，从指定标签的条目提取发布说明。
