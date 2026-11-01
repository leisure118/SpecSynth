# Codex / Claude Code + DeepSeek：LiveFMBench2024 实测

日期：2026-10-30。模型固定为 `deepseek-v4-flash-0731`；总预算 200 秒。输入取自仓库内 `resources/benchmarks/live24/original/`，没有将历史实验规约作为模型输入。

| CLI | 案例 | 最终独立证明 | 耗时（秒） | 原生验证工具执行 |
|---|---|---|---:|---|
| codex | code2_102 | 7/7 | 97.23 | 是 |
| codex | code2_103 | 7/7 | 73.47 | 是 |
| claude-code | code2_102 | 7/7 | 90.01 | 是 |
| claude-code | code2_103 | 7/7 | 65.77 | 是 |

`code2_102` 的最终复测绑定 spec-split、spec-orchestrate、spec-bottomup：两个 CLI 均实际调用 MCP prepare_project 生成 DAG、合约骨架及 stub/inline 切片，再通过原生 verify_candidate 获取真实 Frama-C 诊断。`code2_103` 验证基础 CLI 生成与验证路径。

Codex 使用 Responses API；Claude Code 使用 Messages API。两者均由项目官方 CLI 运行模型/工具循环，API 密钥通过环境或桥接进程 stdin 注入，不读取个人登录记录。Frama-C 以当前固定项目的受控 MCP 工具提供；平台随后独立复核源码 token、原始断言和最终证明。

本报告仅说明两个选定案例接通，不代表整个 LiveFMBench2024 的通过率。原始事件、候选和 WP 日志保存在本机忽略提交的 `runtime/cli-validation/`。

输入 SHA-256：

- `resources/benchmarks/live24/original/code2_102.c`：`dbb299a653dda3174fc7f883aed9b47f3656accd304c9e4ed86f178f4c042325`

- `resources/benchmarks/live24/original/code2_103.c`：`ea17b5573c6ee4d7393b74e4fa427c7eb49a255e148ade2178c9dcf2bb334d98`
