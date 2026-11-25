# AI Skills

个人 AI Agent Skill 集合（去个人化分享版）。

本仓库是产出物同步管道（TWK076）的**公版镜像**：从日常使用的 skill 里挑选、
去除个人信息与内部口径后同步到这里，与公司内部 AI 市场（ai-market）发布同源。

## 安装

把 `skills/<名称>/` 整个目录复制到你的 skills 目录（如 `~/.claude/skills/`、`~/.codex/skills/`），
Agent 即可自动识别（每个 skill 都是一个 SKILL.md 驱动的能力包）。

## 清单

| Skill | 说明 |
|-------|------|
| [ai-content-verify](skills/ai-content-verify/) | AI 内容真伪核验工作流编排器 - 自动核验外部 AI 文章/论坛帖的真实性和技术可行性，并对比现有 Skill 体系判断是否值得补足。触发词：「核验 AI 内容」「这个 AI 工具有真的吗」「评估  |
| [business-report-structure](skills/business-report-structure/) | 汇报结构路由与模板库：先判断汇报场景，再选结构模板。分析型汇报用「背景→问题→假设→论据→总结→backup」；决策型汇报（高层、时间紧、要拍板）用决策版「决策点→方案总览→WHY/WHAT/HOW  |
| [cdp-page-fetch](skills/cdp-page-fetch/) | 裸 CDP（9222）+ Runtime.evaluate 在「已登录页面」里直接调内部接口取数，复用登录态、不依赖 API token 发放。含 iframe native fetch + JS 层 |
| [de-ai-ify](skills/de-ai-ify/) | 文件提交前去 AI 化处理——洗掉 AI 腔、啰嗦表达、结构化痕迹、个人电脑信息。触发词：「去 AI 化」「洗 AI 味」「de-ai」「提交前洗一遍」 |
| [doc-audit](skills/doc-audit/) | 生成检核文档 - 回顾对话中的文档/方案要求，生成标准化检核文档供检核agent审核 |
| [easyocr-image-text](skills/easyocr-image-text/) | 用 EasyOCR 从图片/截图提取文字（中英文，支持中文路径与批量文件夹）。当用户说"读这张图/提取图片文字/OCR/图片转文字/识别图片里的字"时使用。 |
| [goal-gate](skills/goal-gate/) | Goal 模式就绪闸门 - 锁定项目文件夹，对 goal.md + To-Do 文档.md（+ spec.md）做清晰度评分，通过追问补缺直至 ≥90 分才放行 Goal 模式。触发词：「能不能开跑」 |
| [project-folder-init](skills/project-folder-init/) | 标准项目文件夹脚手架生成器，支持两种变体：①通用项目脚手架（goal.md / To-Do 文档.md / 进展看板.html / PRD-进展看板.md / 任务状态.json / 资料文件夹）；② |
| [report-doc-standard-workflow](skills/report-doc-standard-workflow/) | 汇报文档标准生产流程（7 步 + 验证闸门 + 文件夹结构）。当用户要做「业务汇报/分析报告/周报/专题汇报」类文档，或创建/发布任何含数据的协作平台文档（效果评估/阶段复盘/双周报/数据看板说明等） |
| [task-edit](skills/task-edit/) | 待办工具清单任务编辑 - 安全修改任务字段（标题/标签/日期/内容等），核心是「读→合并→写回」三步避免 --tags 覆盖丢标签。当需要改任务标签、改标题、补日期、或批量修字段时使用。触发词：「改一 |
| [wechat-fetcher](skills/wechat-fetcher/) | 微信公众号文章抓取与内容提取工具。使用当需要获取公众号文章内容、提取文章正文、保存为 Markdown 格式时使用。支持自动提取标题、公众号名称、发布时间和正文内容。 |
| [xlsx-data-analysis](skills/xlsx-data-analysis/) | Excel 数据分析工具 - 使用 xlsx2csv 命令行工具将 xlsx 转换为 CSV 格式，便于后续处理和分析。触发词：分析 xlsx 数据、Excel 转 CSV、xlsx 转换、读取 Ex |

---

*最后同步：2026-11-25 11:36（共 12 个）*

> 同步管道：每周自动选品 → 去个人化 → 体检 → 打包 → 发布 AI 市场 → 镜像 GitHub。
