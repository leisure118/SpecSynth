# Rust / Verus 生成工作台

Rust 项目默认进入自然语言生成。左侧选择 NL2VBench 任务、填写描述，或导入 TXT / Markdown / JSON；中间只显示明确打开的文件，未打开文件时保持空白。生成结果先出现在左侧，点击后打开。新建 Rust 项目的 main.rs 为空文件。任务及生成设置按项目缓存在当前浏览器中，切换源码文件不会清空任务；源码仍需保存到项目。

## Agent 与模型分开配置

本平台不使用开发者电脑上的全局 Codex、Claude CLI 或其账号。平台独立安装官方运行时，使用后端保存的 API 配置。运行 `python scripts/install_agent_runtime.py` 安装锁定的依赖。

| Agent | API 格式 | 行为 |
| --- | --- | --- |
| 模型直连 | OpenAI Chat Completions | 保留原 NL2Verus 的生成、验证、反馈修复流程 |
| DeepSeek Harness | OpenAI Chat Completions，需支持 tools | 本项目内置的轻量 Harness，并非 DeepSeek 官方发布的 CLI；模型可以调用受限的 `verify_verus` 工具 |
| Codex | OpenAI Responses | 使用项目私有运行时；不读取用户登录目录；禁用 shell、浏览器和联网工具 |
| Claude Code | Anthropic Messages | 官方 Agent SDK；临时配置目录，禁用内置工具和用户配置 |

Agent 与模型不能任意组合：Chat Completions 的中转接口不能直接作为 Responses 或 Messages 接口。页面只列出协议匹配的模型；服务商是否完整实现所需协议，需用实际运行确认。

在“API 模型”中配置服务地址、接口格式、Model ID 和 Key。地址应是 Base URL，不是完整的 `/chat/completions` 或 `/responses` 路径。Anthropic 地址通常是域名根路径；实际以服务商说明为准。同编号留空 Key 可以保留原 Key。保存不会自动发送付费请求。

配置保存在忽略提交的 `runtime/generation-models.json`，文件权限为 0600。HTTP 响应、项目源码及运行元数据不包含 API Key。这个版本适用于绑定在本机 127.0.0.1 的研究平台；当前仓库没有提供团队用户认证和凭据隔离，不能直接作为多人公网模型配置服务。

## Skills

预置两项规约、循环证明辅助指令，可不选或多选。使用“导入自己的 Skill”上传 Markdown 或粘贴正文。也可以将项目 Skill 放在 `skills/verus/<id>/SKILL.md`。目前加载 Skill 的**指令正文**，不执行其中的脚本，也不声称原生 Skill 工具被调用。

选中的正文和 SHA-256 会冻结到运行记录，生成与每一轮修复都会应用。页面可以查看实际发送的完整提示词。上传的 Skill 保存在忽略提交的 `runtime/generation-skills.json`。

## 运行与实验记录

数据集任务只导入描述与接口；参考答案不会进入模型输入。编辑描述或接口后会切换到自定义任务。RAG 沿用原始独立索引及匹配的 embedding 配置，传入 sample_id 排除当前样本，不降级伪装为向量检索。

每次运行保存项目输入版本、任务、Agent、公开模型配置、Skill 内容快照、每轮提示词、候选代码、Verus 诊断和最终结果。Harness 每次生成最多发出 5 次模型调用、每次最多处理 3 个验证工具调用；外层最多追加 3 轮修复。Codex / Claude 单轮运行最多等待 240 秒；验证器超时单独设置。SDK 自身可能有协议探测和重试，不应用外层轮数作为严格的费用上限。

“生成完成”不等于验证通过。最终通过状态仅由固定版本 Verus 返回，证明绕过标记仍会被原有检查阻止。模型失败、配置缺失和超时不会显示为 Pass。所有新增 Agent 需要对应的可用 API，安装成功不代表模型服务已连通。

官方参考：[Codex 自动化](https://developers.openai.com/codex/noninteractive)、[Claude Agent SDK](https://code.claude.com/docs/en/headless)、[Claude 网关兼容性](https://code.claude.com/docs/en/llm-gateway)。

## 无 API 的界面预览

Rust 生成工作流默认选择 Ground truth 预览，不会调用 API。从 NL2VBench 选择任务后点击“生成 Verus”，会把该样本的真实 verified_verus 作为独立参考文件列出。不会自动打开文件、覆盖项目源文件、写入模型生成记录或计为实验通过。参考文件可以编辑、下载，或通过“加入项目”添加到项目草稿，再点击顶部保存持久化。

纯自然语言文件不包含答案，因此不能伪造 ground truth；可以切换 Agent API 生成。JSON 文件支持 description、function_signature，以及可选的 verified_verus 或 ground_truth。离线输出最近 8 个文件缓存在当前浏览器，真实 Agent 运行仍由后端保存完整历史。

Verus 编辑器保持统一字体颜色，用浅蓝标示 spec 函数、requires/ensures 等规约区域，用浅绿标示可执行函数体内的实现语句，保留导入和独立函数签名的中性背景；用浅橙标示 proof 函数、proof 块、assert、循环不变量和 decreases 终止性条件等证明区域。识别为词法辅助，并非 Verus AST 解析或正确性判断；忽略注释和字符串中的关键字。

## 模型预设

模型下拉框分为“已配置 API”和“模型预设 · 待配置 API”。预设可以直接选中，但不代表已经连通服务，也不会通过配置校验发出付费请求。“配置此模型”会预填名称、协议、Model ID 和官方 Base URL；使用第三方服务时可以改成其实际地址和模型标识。自部署或微调模型可使用“自定义 / 自训练模型”。

模型名称和 ID 于 2026-10-29 核对：[OpenAI 模型目录](https://developers.openai.com/api/docs/models)、[Claude 模型目录](https://platform.claude.com/docs/en/models/overview)、[DeepSeek API](https://api-docs.deepseek.com/)、[DeepSeek 的 Anthropic 接口](https://api-docs.deepseek.com/guides/anthropic_api/)。预设目录只表示配置模板，第三方模型支持情况以服务商为准。
