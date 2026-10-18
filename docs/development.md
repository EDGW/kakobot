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

命令鉴权与帮助共用 `domain/commands.py`。管理 DDL 使用独立的明确授权入口，不放宽普通用户或 AI 修改任务的资源限制。角色批量修改原子替换 JSON；DDL 批量修改与调度共用锁，在一次事务内提交。

各层按职责建立子包，包入口仅说明用途，调用方直接导入实际模块。领域层只保留共享规则与值对象，不依赖应用、存储或展示实现。启动组装集中在 `application/runtime.py`，命令分发集中在 `application/dispatcher.py`。

默认广播内容保留在 `src/UPDATE.md`，由 `infrastructure/storage/broadcasts/updates.py` 每次读取。字体位于 `assets/fonts/`；移动渲染或读取模块时须同步校验资源定位。打包递归收集所有业务 Python 子包，并显式包含更新文案。

```sh
python -m src.tooling.check
ruff check src main.py
python -m src.tooling.package
```

构建输出为 `dist/astrbot_plugin_kakobot-v版本.zip`，包含插件代码、README、docs 和中文字体，不包含 examples、工具脚本、运行数据库、密钥或本地设计草稿。GitHub 标签发布工作流沿用现有配置。

命令文档中，一个 Markdown 文件对应一组功能，在每个命令下分别说明 CHAT、GROUP 的完整格式、所需权限组和行为。参数含义、默认值、作用范围、执行结果及示例直接写在对应命令下，不另设“使用规则与示例”汇总节。普通命令放在 `docs/commands/`，Super 命令放在 `docs/commands/super/`；各目录的 README 维护功能索引。

## 生成文档卡片图片

安装项目依赖后，在仓库根目录运行：

```sh
python -m src.tooling.docs_images
```

脚本递归读取 `docs/` 下的 Markdown，每个文件生成 CHAT 和 GROUP 两张 JPEG。输出到 `docs/pics/` 并保留源目录结构，例如 `docs/commands/ddl.md` 对应 `docs/pics/commands/ddl-chat.jpeg` 和 `docs/pics/commands/ddl-group.jpeg`；`docs/configuration.md` 对应 `docs/pics/configuration-chat.jpeg` 和 `docs/pics/configuration-group.jpeg`。

标题以 `- CHAT` 或 `- GROUP` 结尾的段落只出现在对应会话图片中，整段内容及下级段落一同筛选。公共说明保留在两张图中；某个会话没有命令入口时显示不可用提示。没有会话标记的通用文档生成两份相同正文，页头分别标注会话类型。

排版使用随项目提供的中文字体：命令独立成卡片，行内命令高亮，代码块使用深色底，表格转为逐行信息卡。长命令和中文正文按实际文字宽度换行，图片高度随内容增长，不截断正文。超过 JPEG 高度上限时会报错，可减小字号或拆分源文档。

可以自定义输入、输出、宽度和正文字号：

```sh
python -m src.tooling.docs_images --docs docs --output docs/pics --width 1200 --font-size 25
```

默认宽度1200像素、正文字号25像素。源目录中位于输出目录内的 Markdown 会跳过；重复运行覆盖同名图片，不清理其他文件。`docs/pics/` 为本地生成物，Git 和插件安装包均不包含这些图片；脚本只需 Pillow，不调用模型或网络。
