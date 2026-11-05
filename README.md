# 玄鉴（ACSL AGENT）

面向 C / Rust 的形式化规约生成与验证平台。用户导入源码，选择 Agent、模型、Skill 和验证工具，由平台保存候选、执行独立验证，并根据诊断修复规约。

C 工作台支持 Frama-C / WP 和 VeriFast，复用文件管理、编辑器、运行配置、终端、日志和历史记录；Rust 工作台使用 Verus。界面支持简体中文与 English 切换。

## 主要功能

| 能力 | 当前支持 |
| --- | --- |
| 项目管理 | 导入、新建、文件管理、独立输入快照与运行历史 |
| C / ACSL | 函数契约、循环规约生成与 Frama-C / WP 验证；单文件、终止性及多模块工作流 |
| C / VeriFast | 单文件规约生成、修复和直接验证；使用 VeriFast 分离逻辑规约 |
| Rust / Verus | Rust 代码验证，以及根据需求生成候选并反馈修复 |
| Agent 与模型 | 分别配置 Codex、Claude Code、DeepSeek Harness；支持主模型与可选子模型 |
| 人工协作 | 锁定 C 源码、编辑规约、保存不同的人工版本、版本对比、让 Agent 继续修复 |
| 运行反馈 | 实时步骤、原生 Agent 命令与工具输出、日志、工件和疑似错误行定位 |
| 工具箱 | 函数提取、切片、规约生成与注入、规约检查及验证 |

Agent 负责执行与编排，模型负责生成内容，Skill 提供任务规则，验证器给出证明结果。这些配置相互独立；模型返回“通过”不会被当作验证证据。

## 快速启动

以下命令在本仓库根目录执行，即包含本 README 的 `acsl模块化验证/` 目录。

### 1. 准备依赖

- Python 3.13 或以上，建议使用虚拟环境。
- Node.js 24.9 或以上、npm；官方 Agent 运行时需要该版本。
- 按任务安装 Frama-C / WP、VeriFast 或 Verus。
- 只有使用容器验证或旧 AutoSpec 工作流时才需要 Docker；使用本机验证器时无需启动 Docker。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
npm run build:web
```

Windows 下使用 `.venv\Scripts\Activate.ps1` 激活环境。

### 2. 配置模型与 Agent

首次部署复制模板，在后端填写模型服务地址和密钥；已有 `.env` 时直接编辑，保留现有配置。

```sh
cp -n .env.example .env
python scripts/install_agent_runtime.py
python scripts/install_agent_runtime.py --check
```

安装脚本按部署机器的系统和架构安装项目独立的官方 Agent 运行时，不依赖开发者电脑的全局 CLI。`--check` 只检查依赖，不会调用模型，也不代表模型接口和验证器已就绪。

仅使用“直接验证已有规约”或预置答案时，无需配置生成模型或安装 Agent 运行时。

### 3. 准备验证器

| 验证器 | 本机运行 | 容器运行 |
| --- | --- | --- |
| Frama-C / WP | 安装 `frama-c` 和 Alt-Ergo / Z3，并使后端能够找到它们 | 拉取下方镜像，使用 Compose 的 `verifier` 服务 |
| VeriFast | 执行 `python scripts/install_verifast.py` | 构建 Compose 的 `verifast` 服务 |
| Verus | 安装 `rustup`、`curl` 后执行 `python scripts/install_verus.py` | 统一镜像可在构建时安装固定版本 |

共享 Frama-C 验证默认优先选择本机工具，否则探测专用验证容器。容器模式需要 Docker 服务处于运行状态：

```sh
docker compose pull verifier
```

VeriFast 安装器下载固定的 26.10 官方发行包并校验 SHA-256，当前提供 macOS Apple Silicon 与 Linux x86_64 安装路径。容器方式为：

```sh
docker compose --profile verifast build verifast
```

随后在 `.env` 设置 `VERIFAST_RUNTIME=container`。本机安装则保留 `auto`，或显式使用 `host`。其他安装位置可通过 `VERIFAST_BINARY` 指定。

### 4. 启动服务

```sh
python scripts/run_api.py
```

默认访问：<http://127.0.0.1:8000/>，接口文档：<http://127.0.0.1:8000/docs>。

需要使用其他端口，例如当前本地工作环境的 8010：

```sh
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8010
```

前端由同一服务托管。修改前端后重新执行 `npm run build:web` 并刷新页面；修改后端或模型环境配置后重新启动服务。

## 模型与运行配置

完整变量以 [.env.example](.env.example) 为准，模型目录位于 [configs/models_config.yaml](configs/models_config.yaml)。

| 配置 | 用途 |
| --- | --- |
| `aliyun_API_KEY` | 百炼模型的后端密钥 |
| `BAILIAN_DEEPSEEK_BASE_URL`、`DEEPSEEK_HARNESS_MODEL` | DeepSeek Harness 主模型的服务地址与模型 ID |
| `QWEN35_4B_MIX64_API_BASE_URL`、`QWEN35_9B_MIX64_API_BASE_URL` | 已部署 Qwen 子模型的接口地址，以 `/v1` 结尾 |
| `QWEN_MIX64_API_KEY` | mix64 子模型服务的接口密钥 |
| 对应的 `QWEN35_*_DOCKER_BASE_URL` | 容器可访问的模型服务地址 |
| `ACSL_VERIFIER_RUNTIME` | Frama-C 运行方式：`auto`、`host`、`container` |
| `ACSL_FRAMAC_PROFILE` | Frama-C 验证参数口径：`original` 或 `strict` |
| `VERIFAST_RUNTIME`、`VERIFAST_BINARY` | VeriFast 运行方式及可选可执行文件路径 |
| `VERUS_EXECUTABLE` | 已有 Verus 可执行文件的位置 |

当前百炼主模型配置项为 `deepseek-v4.1-flash-1017`；子模型可选已部署的 `qwen35-4b-mix64` 或 `qwen35-9b-mix64`。模型 ID、接口地址和鉴权必须与实际部署一致，主模型与子模型使用各自配置。

不同 Agent 对接口协议的要求不同：DeepSeek Harness 使用 Chat Completions，Codex 使用 Responses，Claude Code 使用 Anthropic Messages。服务必须实际支持所选协议，不能只改模型名称。Rust 工作台也可通过 API 模型配置添加服务，私有配置保存在 `runtime/generation-models.json`；环境变量部署方式见 `.env.example` 中的 `NL2VERUS_MODEL_*`。

密钥仅放在后端 `.env` 或私有运行配置中，不写入前端源码。服务器与容器必须能够访问配置地址；开发机可访问的内网地址不一定在部署环境可用。同源部署无需额外跨域配置，分离部署时设置 `ACSL_AGENT_ALLOWED_ORIGINS`。

## 使用流程

1. 创建或导入项目，选择需要验证的文件。
2. C 项目选择 Frama-C / WP 或 VeriFast；Rust 项目使用 Verus。
3. 对没有规约的输入，选择 Agent、主模型、可选子模型与 Skill，提交生成并验证任务；已有规约可直接验证，不调用模型。
4. 在右侧查看过程、Agent 终端、日志和验证结果。每次提交保存独立输入，不覆盖已有任务。
5. 验证失败后根据日志和疑似错误行修复，也可保存人工版本并让 Agent 继续。

### 规约编辑与修复

C 工作台仅允许修改规约，前后端共同检查原始 C 源码是否保持不变。可以删除规约注释符号，但未闭合的注释必须补全或完整删除后再保存。

“编辑 Agent 规约的人工副本”保留原 Agent 产物；只有内容不同的人工版本才保留。“保存并让 Agent 继续”提交人工版本的独立快照，不会按每次输入自动调用模型。“仅验证当前规约”只执行验证器。

单案例默认最多追加 3 轮修复，通过后立即结束。DeepSeek Harness 在同一案例内复用官方 CLI 会话，修复已有补丁，不重新派发全量生成。格式错误但有具体规约内容的补丁会进入有界修复，不能当作已验证候选。

任务默认总时限约 200 秒，覆盖生成、修复和独立验证。启用复杂文件自动延长时，多循环、多 C 文件或源码超过 8 KiB 等情况可提高到至少 600 秒；实际预算记录在任务中。总时限与单个证明目标的求解时限不同。

### Skill 选择

| 验证路线 | 内置 Skill |
| --- | --- |
| C / Frama-C | `spec-split`、`spec-orchestrate`、`spec-bottomup` |
| C / VeriFast | `spec-verifast · v1` |
| Rust / Verus | `skills/verus/verus-baseline/SKILL.md` |

VeriFast 任务在执行快照中以新 Skill 替换内置 ACSL 工作流，原版 Skill 和自定义 Skill 保持不变。VeriFast 版本保留自底向上的分析方法，使用独立的分离逻辑语法、权限规则和插入位置；不能直接套用 ACSL。

新版本和案例说明见 [spec-verifast/SKILL.md](resources/skills/spec-verifast/SKILL.md) 与 [案例验证说明](resources/skills/spec-verifast/references/case-validation.md)。案例回归验证的是补丁与真实验证器链路，不代表模型生成成功率。

## 验证结果的含义

- 最终结果依据本次验证器输出和实际工件，生成成功、工具交接完成和证明通过是不同状态。
- Frama-C 展示证明目标数。默认 `original` 参数沿用原有口径，不额外生成 RTE 安全目标，并关闭调用方前置条件目标；通过不能解释为完整运行时安全证明。需要更严格检查时使用 `strict`，不同口径的结果应区分。
- VeriFast 完整验证成功且报告 N 条已验证语句时显示 `N/N`，这是语句统计，不是 Frama-C 证明目标数；失败不推算分母。当前使用 `-safe_mode -enforce_annotations -c -json` 验收 C 编译单元，`-c` 不执行链接检查，也不代表所有外部依赖实现已证明。
- VeriFast 与 ACSL 的契约语法、内存模型和规约位置不同。复杂递归谓词、需要新增 lemma 的任务等仍有适配限制，具体见新 Skill 的案例说明。
- 超时、工具不可用、无有效候选和未证明均不能计为通过。红色行号表示诊断或疑似未证明位置，不等于已经找到程序反例；源码变更后应重新验证。

## 项目结构与运行产物

```text
acsl模块化验证/
├── apps/             Vue 前端、FastAPI 接口与服务装配
├── acsl/             领域、应用用例、适配器与基础设施
├── engine/           规约补丁、Agent 协议与验证器实现
├── configs/          模型、示例和 Agent 依赖锁定配置
├── resources/skills/ 内置 C Skill 及 VeriFast 案例
├── skills/verus/     Rust / Verus Skill
├── docker/           独立验证器镜像构建文件
├── scripts/          启动、安装与构建脚本
├── tests/            后端与浏览器测试
├── docs/             专题文档
└── runtime/          本机运行数据与安装的工具，不提交到 Git
```

| 位置 | 内容 |
| --- | --- |
| `runtime/projects/` | 项目文件、配置及人工版本 |
| `runtime/runs/<task_id>/` | `task.json`、`result.json`、输入快照和任务工件 |
| `runtime/verifast/<id>/` | VeriFast 输入、命令、源码哈希、原始日志和结果 |
| `runtime/skills/` | Skill 版本记录 |
| `runtime/cli/` | 项目管理的 Agent 运行时 |
| `runtime/generation-models.json` | 私有 API 模型配置 |

迁移服务时保留 `.env` 和必要的 `runtime/` 数据；CLI 与验证器按目标机器重新安装，不直接复制不同系统或架构的二进制。

## 部署与开发

统一服务镜像使用 [docker-compose.unified.yml](docker-compose.unified.yml)：

```sh
docker compose -f docker-compose.unified.yml up -d --build
```

该镜像按 Linux amd64 构建，Agent 运行时安装在持久化数据卷之外，`runtime/` 用于保存运行数据。VeriFast 不由此镜像自动安装，需另外准备并配置可用的运行时。部署模型地址使用服务器或容器可达的地址；对外多人使用还需补充用户认证、配额和任务隔离。

后端按 `apps/api → acsl.application → acsl.domain / adapters` 分层，验证器通过独立适配器接入。结构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，Rust 专题见 [docs/RUST-WORKFLOW.md](docs/RUST-WORKFLOW.md) 与 [docs/verus-generation.md](docs/verus-generation.md)。

后端测试需另外安装 `pytest`；浏览器测试需准备 Playwright 浏览器及相应测试依赖。修改文档无需启动模型实验，验证工具相关测试则需要对应的真实工具链。

```sh
python -m pytest tests/test_architecture.py tests/test_workspace_api.py tests/test_verifier_dispatch.py -q
npm run build:web
```
